# Task Resource Lifecycle (内存优化)

`workflow-skill` owns this contract. Treat task work as a resource stack: acquire only what the exact task needs, record ownership before use, preserve the delivered result, then release resources as soon as their last real consumer is finished. The ledger is an audit and coordination mechanism, never a background janitor and never a controller for Codex tasks, threads, sessions, or Endings.

## Ownership and classification

- Create one exclusive `Cache/tmp-<task>` root only after proving that it did not already exist. Bind its ledger and ownership marker to the exact project, task root, and task. Never adopt another task's root or search for something that merely looks disposable.
- One-task files, logs, downloads, renders, debug fixtures, and ordinary test scratch are disposable only when the task reserved their exact absent path below its own `Cache/tmp-*` root and later sealed the created identity. Reusable formal tests stay in source.
- `Cache/<YYYYMMDD>/` is short-term retained material and requires a retention reason plus a next review point. `Cache/remote-*` and `Cache/remote-test/` require explicit user or project-contract retention and are never auto-deleted.
- Preexisting, user-opened, shared, unsaved, concurrent, Unity/tool-managed, operating-system-managed, or otherwise ambiguous resources are `preexisting`, `retained`, or `deferred_conflict` and remain untouched.
- Runtime resources are exact task-created typed handles: a process/server requires PID, start time, executable, and working-directory identity; a browser tab or application window requires its exact task-created context/window/instance identity. Names, ports, broad process matching, `killall`, and `pkill` never prove ownership.

## Stack, handoff, and barriers

Model independent graph branches as separate stacks. Model a shared resource with an explicit consumer map; derive outstanding use from that map rather than a mutable guessed reference count. Register every downstream or Ending handoff before sealing or release begins. A missing, blocked, cancelled, or timed-out consumer is not silently treated as finished.

A disposable resource may enter cleanup only after three independent facts are durable:

1. the final user result is stored outside the disposable target and read back with a digest;
2. every explicit consumer has supplied its own exact readback; and
3. when an Ending consumes the resource, its evidence and terminal record are stored outside the disposable target and read back first.

Release each branch in reverse acquisition order after those barriers. Independent branches may release independently. A producer releases producer-only resources after result delivery and hands off only the resources still needed downstream. Ending releases only exact resources it created or received by explicit handoff, after evidence persistence, and remains globally visible.

## Filesystem release

Before deletion, revalidate the project, Cache root, exclusive task-root marker, lexical ancestors, sealed target identity, filesystem boundary, and exact path. Reject symlinks, reparse points, mount crossings, identity drift, overlapping paths, or unexpected content as a conflict. Persist `cleanup_in_progress`, move only the recorded lexical entry to its predeclared same-root quarantine, recheck identity, remove without following links, verify absence, and only then record `released`. If it was already absent, record `released_external`; if cleanup fails, record `cleanup_failed`. Never mark a resource released before the observable release.

`deferred_conflict` is revalidatable, not a permanent excuse and not permission for a retry loop. A later related task may explicitly revalidate the exact target and either resume or record an independently observed external release. There is no background scan or cleanup.

## Runtime and UI release

The ledger never kills a process, clicks a window, closes a tab, or controls software itself. The same owner tool or typed adapter that opened the exact resource performs a graceful close and returns an identity-bound receipt with an exact-handle-absent readback. Only that structured receipt may move a runtime resource from `cleanup_ready` to `released`. An identity mismatch, unsaved document, shared/preexisting app or Unity instance, tool timeout, or failed close becomes `deferred_conflict` or `cleanup_failed`; there is no broad or forceful fallback.

No resource cleanup or reclamation operation may message, interrupt, terminate, archive, delete, or otherwise control another Codex task, thread, session, or Ending. This restriction does not change the separate Verify repair handoff protocol; cleanup can never be used to trigger it.

## Portable ledger

Use `scripts/task_resource_ledger.py` for deterministic `init`, `acquire-path`, `seal-path`, `acquire-runtime`, `record-retained`, `record-preexisting`, `durable-readback`, `consumer-readback`, `handoff`, `evidence-persisted`, `prepare-release`, `cleanup-path`, `confirm-runtime-release`, `defer-conflict`, `resolve-conflict`, and `show` operations. It stores project-relative paths, hashed task keys, exact identities, monotonic audit events, and atomic JSON updates under an exclusive lock. `show` emits only aggregate state, and the implementation exposes no process-control or Codex task-control primitive.

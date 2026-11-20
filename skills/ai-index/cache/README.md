# Cache ownership and current state

At task start/resume, read this folder, execute Workflow's Cache cleanup
checkpoint before allocating new support or implementing the task, then refresh
with Management's `project_ai_index.py cache --project-root ROOT --apply`.
Listing files or refreshing inventory alone does not complete startup cleanup.
Repeat cleanup and refresh at finish and after consumption or retention changes.
The project owns its cache policy here; `current.json` is a bounded replacement
of current operational state, never a memory log. Missing paths disappear on
refresh; failed native checks keep exact items visibly pending.

- Before implementation, plan deletion, final destinations and exact necessary retained files with consumers and ending conditions. No shared scratch pools, convenience backups or speculative review/reuse retention. Each verified and reported result triggers immediate delivery cleanup, even in the same chat.
- Task support and any undeclared new Cache output belong to a fresh
  `Cache/temp-*` run. Release unused exports, builds, copied projects and other
  intermediates immediately after the required output handoff. A verified upload
  can finish the local package's purpose before unrelated backend work completes.
- Local debugging keeps only its actual live inputs; requested final results leave scratch through verified owner handoff. Retain only exact necessary active/recovery inputs or explicit user holds; remove unrelated files before retention.
  Failed, stopped or abandoned task support is due for cleanup after 72 hours
  without heartbeat or descendant changes, after fresh native consumer checks.
  Active resources, real recovery dependencies and canonical originals remain
  protected; age alone does not delete them.
- Canonical assets, configuration and service/runtime data keep their native
  owners. Describe project-specific owners in this README or optional
  `owners.json`; cleanup must use the actual native owner.
- Reserve `remote-*` for exact payload files required by a lasting consumer
  under a Git-tracked contract with a native destination and sync route.
  Verify current bytes and synchronized readback through that owner. All
  generated intermediates and test outputs go directly to `temp-*`.
  Inventory metadata supplies review pointers. Check exact owners before any
  cleanup.
- Codex sessions, databases and managed worktrees are user-managed and excluded.

The Workflow registry at `Cache/temp-task-cache-registry` owns exact task
identity, heartbeat, retention and deletion proofs. The ignored `current.json`
summarizes that registry and immediate Cache children without traversing remote
payloads. An inventory row is not permission to delete. Keep current state
ignored in Git; stable owner rules remain versioned. Do not add one file per run.
An existing `remote-task-cache-registry` is local control compatibility, not a
remote resource or disposable payload; preserve its active native owner.

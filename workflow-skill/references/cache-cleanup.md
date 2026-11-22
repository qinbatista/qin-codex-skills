# Requested Cache cleanup

Use this workflow when the user requests Cache or `temp-*` cleanup, or for exact predecessor runs selected by the [automatic task-transition checkpoint](task-resource-lifecycle.md#task-transition-cleanup-checkpoint). The request authorizes deletion of eligible temporary support within the selected scope. Complete independent safe cleanup without asking again; retain only exact necessary inputs and source/native owners.

Automatic checkpoints clean exact predecessors and registered completed/obsolete disposable runs immediately after fresh guards pass. Foreign working runs require at least 48 hours without activity. This standing authorization does not require another request. Broad filesystem discovery builds the index when requested; subsequent checkpoints use that local index rather than repeatedly traversing the whole computer.

## Local index and executable checkpoints

Run `scripts/task_cache_cleanup.py` from the installed Workflow Skill. Its local operational registry holds the exact project/task/run identity and cleanup plan. Allocation registers a default plan before payloads: `delete: ["."]`, `outputs: []`, `retain: []`, `trigger: "verified-result-reported"`, and a purpose. Describe the actual unit purpose before implementation. Refine only needed destinations/retention through `plan`; never register source or native runtime data as disposable.

A plan has this shape (paths are per-run data, not maintained configuration):

```json
{
  "purpose": "verify and deliver the requested result",
  "delete": ["."],
  "trigger": "verified-result-reported",
  "outputs": [{"path": "<absolute final file outside task Cache>", "sha256": null}],
  "retain": []
}
```

Before handoff, replace an output's null hash with its verified SHA-256. `delivery` and `finish` refuse cleanup if a declared final file is absent or differs. Source-only or chat-only results use an empty output list. Each necessary retained input has `path` (exact run-relative file/subdirectory, never `.`), `kind` (`active-input|recovery-input|user-hold`), `consumer`, `reason`, and `until` (the event ending that need). User holds require the user's explicit request. Generic review, reuse, saving setup, shared pools and backup insurance are insufficient. `touch --state retained|recovery` rejects a reason without this plan and rejects unrelated payloads left beside its exact retained inputs. Write the plan JSON temporarily inside the run, apply it, and remove that transport file before retention.

```text
python task_cache_cleanup.py scan --project-root PROJECT
python task_cache_cleanup.py plan --project-root PROJECT --task-id THREAD --run-root RUN --plan RUN/plan.json
python task_cache_cleanup.py checkpoint --project-root PROJECT --task-id THREAD --phase start --current-run RUN --apply
python task_cache_cleanup.py checkpoint --project-root PROJECT --task-id THREAD --phase delivery --current-run RUN --apply
```

Use resolved absolute project/run paths and the host's Python 3 interpreter. At the first verified and reported result, call `delivery` immediately, even while the chat and later units continue. It removes the exact disposable run and registration without an age delay; `finish` remains a compatible alias. Deliver final files outside task Cache and remove unnecessary attempts, logs and intermediates. Retention blocks whole-run delivery until the necessary files have a verified owner handoff or their actual consumer is explicitly retired. No backup or renamed folder is created by cleanup.

Run start, transition and finish checkpoints before new work and at delivery. Indexed completed or obsolete runs and resumable deletions take priority over the idle scan. Use the 48-hour fallback for abandoned runs. Existing 72-hour retention records are reviewed at the new threshold. A recorded `user-hold` survives automatic expiry, including while its run is still marked working. Release it through the exact owner after the user ends the hold. Review legacy reason-only retention through the original owner.

On Darwin, read process metadata before launching lsof. Validate states only for identified lsof observers; unrelated Darwin `?`/`?E` process states do not suppress cleanup. Unknown lsof state remains pending, and the native handle/process probes still run. An existing lsof in an uninterruptible kernel wait makes the affected native check pending and suppresses another observer launch, including parenthesized executable names. A caller timeout or kill request does not prove that native I/O or descendants exited; `-b` and `-S` do not cover every mounted-directory attribute call. Preserve affected payloads, report exact pending PIDs, and never disconnect backup mounts or disturb Codex as an automatic repair.

Explicit finished/obsolete runs are processed before unrelated records. Confirm `requested_complete: true` for the exact run. The command exits nonzero when the requested run remains, including when an active consumer produces `keep`. It also reports unrelated pending results independently. Use `--requested-only` to close one verified finished or obsolete run without retrying unrelated owners. Repeating an exact completed finish is idempotent.

Use the [allocator's continuation command](project-cache-artifact-policy.md#separate-executions-and-continuation) when a new execution replaces an exact old run of the same task. Its cleanup proof binds the verified successor and the original old-run inventory so an interrupted cleanup can resume without another allocation.

Before its first unlink, the helper persists a bounded compressed inventory bound to the original owner, volume/inode, member identities and file change times. Interrupted or budget-limited deletion keeps that proof and the precise error. The next checkpoint may resume only its unchanged remaining subset after fresh native consumer checks. New/modified/replaced members, changed retention, invalid proofs and legacy blocked records without original proof require exact owner review; never invent a new snapshot to make a blocked deletion pass. Remove the payload, proof and registry entry with absence readback. Control writes use one pending slot per record, and a bounded native lock pool releases crashed writers without accumulating per-run lock files; live or unverified legacy locks remain protected.

Registered parents and descendants keep their separate lifecycle: a child cannot bypass its parent's protection, and parent deletion waits for each independently registered child to close, including a completed child whose registration still exists. Close nested owners from the inside outward; do not erase a pending child by deleting its enclosing run.

Project path spellings may share one Cache on a case-insensitive filesystem. Verify their native directory identity and use the existing run registration and its original spelling. Multiple registrations for one physical run require owner reconciliation. For a run over the inspection bound, close unrelated verified owners independently and use the producer's native cleanup route for the oversized run. Allocate separate registered runs for independently delivered stages so new runs stay within the inspection bound.

Tests must close their registered fixture owner through the public exact checkpoint on success, setup/body failure, timeout and cooperative cancellation. Close subprocesses and cleanup callbacks first. When borrowing a caller's existing `CODEX_PROJECT_CACHE_ROOT`, delete only the inner fixture and leave the outer owner, registry and siblings intact. Removing the directory alone or swallowing a teardown error does not close its registered lifecycle. Surface unresolved cleanup and stop replacement allocation rather than repeatedly generating copies.

Project Cache checkpoints also inspect the existing default legacy external ledger when it contains this exact project's registration. Filter the shared legacy run records by their exact project owner before inspecting payloads; other projects' records remain with their owners. For a configured older store, pass its exact existing base with `--artifact-root` to `scan`, `checkpoint` or `release-retention`. This is cleanup compatibility only: new allocation, registration and working output remain project Cache only. A legacy run still needs its original project/task/run identity, concrete retirement, unchanged payload and native consumer checks; existing retention and native-ledger barriers remain in force. Never silently abandon the old ledger when changing the allocation policy.

On macOS, newly registered runs also bind the native volume UUID. A changed device number after reboot is accepted only with that original UUID and unchanged inode; records without original stable-volume proof remain pending rather than adopting a replacement directory.

Discovery reports Cache directories and naming violations without granting deletion eligibility. For legacy support, first establish actual purpose and consumers, then use `register --project-root PROJECT --task-id THREAD --run-root EXACT --reason EVIDENCE --state complete`. Unknown entries remain review candidates, not permanent exemptions: inspect their source/receipts, clean confirmed disposable contents and register eligible runs. Use the original owner for existing ledgers and Git worktrees. Missing/failed activity probes, changed identities, escaping links and concrete retention/recovery needs block only the affected candidate.

For confirmed release, use `release-retention --project-root PROJECT --task-id THREAD --run-root EXACT --run-id REGISTERED_ID --identity DEVICE INODE --reason OWNER_RELEASE`. Record the actual verified consumption, cancellation, or release of the user hold. Read identity from the existing registry record. The command requires matching ownership, unchanged payload identity and clear native consumers before marking the run complete. The checkpoint completes deletion through its ordinary guards. An explicit `user-hold` stays protected until its owner releases it. Resume blocked runs through their existing deletion proof or exact owner review.

On macOS/Linux, the native consumer probe reads the current open-handle inventory with NUL-delimited names and matches the exact directory boundary, then checks process references. It does not make `lsof` recursively walk a large build tree. On macOS, a `can't stat()` warning becomes `scope_warnings` only when the current mount table proves the warned SMB filesystem is a nonlocal mount outside the exact local target and its descendants. Target or nested mounts, other filesystems, unknown warnings, incomplete inventories, errors and timeouts remain blocking; never suppress stderr or infer an empty consumer list from a failed probe. On Windows, inspect every owned member with native file-process IDs, including directory working handles, and check readable process command lines for exact run references. Protected process arguments can be unavailable; their open handles remain covered by the native file query. Failed or malformed native file inventories remain pending.

Other tasks' 48-hour inactivity is measured from the newest heartbeat and recursive file/directory changes, not just the top folder date. A live producer or open consumer protects its exact resources; a chat that remains open does not protect unused siblings. Checkpoints apply the same fresh identity, boundary and consumer checks immediately before deletion and read back absence. Keep unrelated siblings intact. Hosts without a supported consumer probe report pending.

## End-goal consumption and bounded current index

Upload/submission goals consume local IPA/AAB/APK, archives, native exports and frozen build inputs after authoritative acceptance and any exact pending import/native callback finishes. Do not wait for unrelated backend processing or keep a local package solely because it is newest. A failed/cancelled upload retains only concrete retry inputs while active; 48 idle hours makes that task support eligible at the next task checkpoint. Ordinary tests keep requested video/results with their real owner and immediately discard unused test projects, build output and intermediate captures. Local debugging keeps only its currently consumed workspace. Native retained-resource owners remain responsible for partial deletion.

The project AI-index `cache/` owns concise stable rules and a bounded ignored `current.json`, not a growing log or a second copy of the registry. Read the owner map at startup; after allocation, deletion, retention or remote-owner changes refresh it through Management’s `cache --apply` command. Removed paths and expired registry entries must disappear. Never auto-remove Codex chats, sessions or databases, or create Ending chats for cleanup.

The local control registry is `Cache/temp-task-cache-registry`; the older `remote-task-cache-registry` spelling remains supported only for an existing live lock domain. It is local operational state, not synchronized content or a disposable payload. Do not rename a live registry, create both, or adopt either for deletion.

## Project Cache naming and producer repair

Use a fresh `Cache/temp-*` run for all task support and any new Cache output with no clear owner or sync contract. Other Cache names such as bare `build`, `tests`, `tmp-*` and loose task outputs require producer repair. The [artifact policy](project-cache-artifact-policy.md) defines the exact `remote-*` exception.

Review `remote_review` from scans and checkpoints against the Git-tracked contract, exact allowlist, native sync route and lasting consumer. Allocation diagnostics show the total and at most five candidate paths. Retire confirmed completed test payloads after consumer checks and fix in-scope writers that would recreate them. For each authorized remote deletion, select exact keys and read back absence through the native route.

Treat every nonconforming entry as a defect to resolve now: locate the writing code/configuration/instruction, stop that producer from recreating the path, and delete its obsolete build/test material. If the entry mixes current inputs or unique requested results with scratch, hand only those necessary files to their real owner, update consumers, verify bytes, then delete the obsolete directory. Never fix this by merely adding `remote-` to garbage or by deleting live inputs. Package source trees, browser profiles and runtime caches nested inside their owning run are not independent project Cache roots; their native layouts must not be recursively renamed. A source directory named `cache` is not automatically disposable.

## Select the requested scope

| User request | Discovery scope |
| --- | --- |
| One project, Cache or temporary directory | Only the named project's owners or exact selected directory. An unqualified “this project” means the current project. |
| All Codex projects | Use `list_projects` and current chats/worktrees to enumerate exact project roots and hosts; deduplicate roots and their artifact owners. Include projects outside the current workspace. |
| The whole computer | Enumerate accessible local volumes and discover Skill-generated `Cache/temp-*` directories and configured project Cache task stores. Do not reduce this to the current workspace or only registered Codex projects. |

Do not expand a single-project request to other projects. Whole-computer scope covers accessible storage on this computer; remote hosts require their own requested scope. Report unavailable hosts, volumes, permissions or incomplete inventories rather than claiming exhaustive cleanup.

## Check exact runs and consumers

Before deletion, inspect native Codex project/chat status with `list_threads`, `wait_threads` or exact `read_thread` calls as needed. Map tests, builds, external jobs, workers and worktrees to their exact run roots and consumed resources. Protect only source/native owners and the exact necessary active/recovery inputs or explicit user holds, including current cleanup inputs. An active project/chat does not protect completed sibling runs; an open or idle chat alone proves neither use nor disposability.

Treat paused, failed, resuming, approval-waiting or unknown runs as protected only where actual recovery or active-use needs remain. If a candidate's consumers cannot be established, retain that candidate and report the gap; continue other eligible runs, including in the same project/chat. Do not stop active jobs, close user apps, interrupt chats or wait for the whole project to finish to release an independent completed run.

## Startup countdown for recent tasks

When the user opts in, use the user-level Codex `developer_instructions` setting to start one countdown per real local task start or resume, including a projectless request. Start it inside that request after any required project admission. The default delay is 60 elapsed seconds and can be set with `--delay-seconds`. Keep the exact running command handle in the active task and continue independent work. On `ready`, inspect recent task receipts once and close the countdown handle. Finish the review in the same request.

```text
python task_cache_cleanup.py recent-countdown --task-id CURRENT_TASK --delay-seconds 60
python task_cache_cleanup.py inspect-run --project-root PROJECT --task-id REGISTERED_TASK --run-root EXACT_RUN
```

After the countdown, use the Codex chat inventory and [recent task evidence](ending-resource-audit.md#select-by-purpose) to select up to ten relevant local chats. Read their actual tool receipts to bind each run path and producer to its owning task and verified outcome. Use the registered task identifier even when it differs from the chat identifier. Group related results by recent task. Verify payload and registration absence for closed work, report disposable leftovers with their exact paths and reasons, and keep active work, user holds and current recovery inputs protected. Report an unknown owner or unavailable readback as pending.

`inspect-run` checks one run read-only. `eligible` includes measured bytes after the native guards pass. `absent` with a registered `state` still has a ledger entry. `pending` reports missing ownership or the exact guard that prevented classification. Treat `eligible` as current evidence for the audit. Any authorized deletion needs a fresh apply checkpoint. Keep the review within those receipts and use the owning tool for non-Cache resources. The countdown has no calendar state and runs only for the active request.

For an explicitly requested project-wide cleanup, use the manual `sweep --task-id TASK --project-root PROJECT_A --project-root PROJECT_B --apply`. Read back `directories_deleted`, `bytes_deleted`, `pending_count`, and the owner-review entries. Verify the original producer and its handoff before registering unregistered support. Use `--skip-cache-index` for registration in another selected project and keep reference indexes outside that sweep.

## Traverse and delete eligible temporary directories

1. For each selected project, inspect its known Cache owners and use `project_artifact_directory(project_root, create=False)` from [the path resolver](../scripts/task_artifact_paths.py) for its project Cache task store. Current support uses `Cache/temp-<task-key>-<run-id>/`; older external `t-<task-key>/` and project `Cache/temp-*` are compatibility/cleanup inputs only. New executions always follow the [project Cache artifact policy](project-cache-artifact-policy.md).
2. Discover `temp-*` directories directly beneath Cache owners, including owned Cache folders nested within the requested scope. Whole-computer discovery also checks non-Codex project roots and configured external stores. Do not match arbitrary `temp-*` elsewhere, traverse symlinks/junctions/reparse points, or enter Codex-managed storage, system/virtual stores or unrelated application caches. Inaccessible branches stay pending.
3. Confirm the candidate is Skill-generated disposable support from a finished unit with no remaining consumer. Use project rules, producer/run history or ownership records. Existing directories may be cleaned even when this chat did not create them. Use the continuation command for an exact predecessor with useful inputs. Preserve source, canonical runtime/assets, memory vaults, requested final outputs in their actual owner, unsaved work and exact necessary recovery inputs. Resolve missing retention metadata against the original producer and consumer before deciding disposal.
4. Recheck exact run/resource activity, consumers and directory identity immediately before each deletion. Resolve and bounds-check the candidate against its selected Cache or external project owner. The guarded helper may unlink internal symlinks and closed FIFO/socket nodes without following them after native consumer checks; reject escaping links, reparse points, hard links, device nodes and mounts. Use portable native filesystem operations and delete only the selected disposable directory, never its entire Cache, project or artifact base. For an existing resource ledger, use its owner/helper and honor its retention and release barriers. An eligible legacy `Cache/temp-*` can be deleted directly under this request; moving it elsewhere is unnecessary. Release disposable worktrees through [their native owner](task-resource-lifecycle.md#worktrees-and-disposable-checkouts), never as ordinary directory trees.
5. Read back each deleted path's absence and preserve unrelated siblings. Continue after a candidate fails; report the exact inaccessible, active, retained or uncertain item. Remove an empty task directory only when its ownership is verified. Report directory counts and measured disk bytes when available; do not claim RAM savings from file deletion.

Finish with the requested scope, actual removed run directories and worktrees, naming defects, exact active or retained skips, and remaining coverage limits. Use the explicit trigger requested by the user for recurring cleanup. The automatic [Ending resource audit](ending-resource-audit.md) uses the same indexed due-run pass alongside its bounded originating and recent-chat checks.

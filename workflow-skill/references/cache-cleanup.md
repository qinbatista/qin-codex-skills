# Requested Cache cleanup

Use this workflow when the user requests Cache or `temp-*` cleanup, or for exact predecessor runs selected by the [automatic task-transition checkpoint](task-resource-lifecycle.md#task-transition-cleanup-checkpoint). The request authorizes deletion of eligible temporary support within the selected scope. Complete independent safe cleanup without asking again; preserve exact active, recovery, shared and review/reuse resources.

Automatic checkpoints clean exact predecessors and registered disposable runs from other tasks that have had no activity for at least 24 hours. This standing authorization does not require another request. Broad filesystem discovery builds the index when requested; subsequent checkpoints use that local index rather than repeatedly traversing the whole computer.

## Local index and executable checkpoints

Run `scripts/task_cache_cleanup.py` from the installed Workflow Skill. The project Cache operational registry records project, task, exact run identity, heartbeat and disposition; it is operational cleanup state, not project memory. Allocating with `task_artifact_paths.py --create` registers a fresh project Cache run. Keep producers current through `touch`; do not register real source, assets or final deliverables as disposable. `touch --state retained|recovery --reason REASON` requires the concrete current consumer, user review or minimum retry input and schedules review within 24 hours. An allocation reason is not retention evidence. Missing or due retention reasons surface as pending owner review, never permanent silent exemptions or automatic deletion permission; inspect the exact need and renew it or release the retired run.

```text
python task_cache_cleanup.py discover --project-root PROJECT --search-root PROJECTS --apply
python task_cache_cleanup.py scan --project-root PROJECT
python task_cache_cleanup.py checkpoint --project-root PROJECT --task-id THREAD --phase start --current-run CURRENT --obsolete-run PREVIOUS --apply
python task_cache_cleanup.py checkpoint --project-root PROJECT --task-id THREAD --phase transition --current-run CURRENT --obsolete-run PREVIOUS --apply
python task_cache_cleanup.py checkpoint --project-root PROJECT --task-id THREAD --phase finish --current-run CURRENT --apply
```

Use resolved absolute project/run paths. Omit `--current-run` when no run has been allocated; repeat `--obsolete-run` for exact retired predecessors. `finish` declares that delivery and any necessary retention/recovery handoff have already been verified. It removes the current disposable run and its registry entry. Call these commands in the active task; the Skill is not an OS scheduler or a Codex startup hook.

Project Cache checkpoints also inspect the existing default legacy external ledger when it contains this exact project's registration. For a configured older store, pass its exact existing base with `--artifact-root` to `scan`, `checkpoint` or `release-retention`. This is cleanup compatibility only: new allocation, registration and working output remain project Cache only. A legacy run still needs its original project/task/run identity, concrete retirement, unchanged payload and native consumer checks; existing retention and native-ledger barriers remain in force. Never silently abandon the old ledger when changing the allocation policy.

On macOS, newly registered runs also bind the native volume UUID. A changed device number after reboot is accepted only with that original UUID and unchanged inode; records without original stable-volume proof remain pending rather than adopting a replacement directory.

Discovery reports Cache directories and naming violations without granting deletion eligibility. For legacy support, first establish actual purpose and consumers, then use `register --project-root PROJECT --task-id THREAD --run-root EXACT --reason EVIDENCE --state complete`. Unknown entries remain review candidates, not permanent exemptions: inspect their source/receipts, clean confirmed disposable contents and register eligible runs. Use the original owner for existing ledgers and Git worktrees. Missing/failed activity probes, changed identities, links and concrete retention/recovery needs block only the affected candidate.

After the actual owner explicitly retires a retained/recovery input, use `release-retention --project-root PROJECT --task-id THREAD --run-root EXACT --run-id REGISTERED_ID --identity DEVICE INODE --reason OWNER_RELEASE`. Read the exact identity from its existing registry record; never adopt a replacement directory. The command requires matching ownership, unchanged payload identity and clear native consumers, then marks the run complete for an ordinary checkpoint. It does not delete files, release another native ledger, or permit blocked-run recovery. Ordinary `touch` and `finish` keep their retention barrier.

On macOS/Linux, the native consumer probe reads the current open-handle inventory with NUL-delimited names and matches the exact directory boundary, then checks process references. It does not make `lsof` recursively walk a large build tree. On macOS, a `can't stat()` warning becomes `scope_warnings` only when the current mount table proves the warned SMB filesystem is a nonlocal mount outside the exact local target and its descendants. Target or nested mounts, other filesystems, unknown warnings, incomplete inventories, errors and timeouts remain blocking; never suppress stderr or infer an empty consumer list from a failed probe.

Other tasks' 24-hour inactivity is measured from the newest heartbeat and recursive file/directory changes, not just the top folder date. A live producer or open consumer protects its exact resources; a chat that remains open does not protect unused siblings. Checkpoints apply the same fresh identity, boundary and consumer checks immediately before deletion and read back absence. Keep unrelated siblings intact. Windows without a supported consumer probe must report pending, never silently treat that as no activity.

## Project Cache naming and producer repair

Project Cache direct child directories may only use `temp-*` for disposable task support or `remote-*` for a verified resource owner. Do not create bare `build`, `tests`, `local-test-artifacts`, `ios-runtime-evidence`, `tmp-*`, date-only or task-title directories, or loose task outputs. New task support goes to a fresh project-owned `Cache/temp-*` run under the project Cache artifact policy.

Treat every nonconforming entry as a defect to resolve now: locate the writing code/configuration/instruction, stop that producer from recreating the path, and delete its obsolete build/test material. If the entry mixes current inputs or unique requested results with scratch, hand only those necessary files to their real owner, update consumers, verify bytes, then delete the obsolete directory. Never fix this by merely adding `remote-` to garbage or by deleting live inputs. Package source trees, browser profiles and runtime caches nested inside their owning run are not independent project Cache roots; their native layouts must not be recursively renamed. A source directory named `cache` is not automatically disposable.

## Select the requested scope

| User request | Discovery scope |
| --- | --- |
| One project, Cache or temporary directory | Only the named project's owners or exact selected directory. An unqualified “this project” means the current project. |
| All Codex projects | Use `list_projects` and current chats/worktrees to enumerate exact project roots and hosts; deduplicate roots and their artifact owners. Include projects outside the current workspace. |
| The whole computer | Enumerate accessible local volumes and discover Skill-generated `Cache/temp-*` directories and configured project Cache task stores. Do not reduce this to the current workspace or only registered Codex projects. |

Do not expand a single-project request to other projects. Whole-computer scope covers accessible storage on this computer; remote hosts require their own requested scope. Report unavailable hosts, volumes, permissions or incomplete inventories rather than claiming exhaustive cleanup.

## Check exact runs and consumers

Before deletion, inspect native Codex project/chat status with `list_threads`, `wait_threads` or exact `read_thread` calls as needed. Map tests, builds, external jobs, workers and worktrees to their exact run roots and consumed resources. Protect only those resources still needed by live, recovery, shared or review/reuse consumers, including the current cleanup run. An active project/chat does not protect completed sibling runs; an open or idle chat alone proves neither use nor disposability.

Treat paused, failed, resuming, approval-waiting or unknown runs as protected only where actual recovery or active-use needs remain. If a candidate's consumers cannot be established, retain that candidate and report the gap; continue other eligible runs, including in the same project/chat. Do not stop active jobs, close user apps, interrupt chats or wait for the whole project to finish to release an independent completed run.

## Traverse and delete eligible temporary directories

1. For each selected project, inspect its known Cache owners and use `project_artifact_directory(project_root, create=False)` from [the path resolver](../scripts/task_artifact_paths.py) for its project Cache task store. Current support uses `Cache/temp-<task-key>-<run-id>/`; older external `t-<task-key>/` and project `Cache/temp-*` are compatibility/cleanup inputs only. New executions always follow the [project Cache artifact policy](project-cache-artifact-policy.md).
2. Discover `temp-*` directories directly beneath Cache owners, including owned Cache folders nested within the requested scope. Whole-computer discovery also checks non-Codex project roots and configured external stores. Do not match arbitrary `temp-*` elsewhere, traverse symlinks/junctions/reparse points, or enter Codex-managed storage, system/virtual stores or unrelated application caches. Inaccessible branches stay pending.
3. Confirm the candidate is Skill-generated disposable support from a finished unit with no remaining consumer. Use project rules, producer/run history or ownership records; directory name, age, size or an idle chat alone is insufficient. Existing directories may be cleaned even when this chat did not create them. For continued work, verify selective copies of useful inputs into its newly allocated run before retiring the old dependency; never copy the entire scratch tree. Preserve source, canonical runtime/asset caches, memory vaults, requested outputs, review/reuse environments, shared resources, unsaved work and minimum recovery inputs. Missing retention metadata is not deletion permission.
4. Recheck exact run/resource activity, consumers and directory identity immediately before each deletion. Resolve and bounds-check the candidate against its selected Cache or external project owner; reject links anywhere in the tree. Use portable native filesystem operations and delete only the selected disposable directory, never its entire Cache, project or artifact base. For an existing resource ledger, use its owner/helper and honor its retention and release barriers. An eligible legacy `Cache/temp-*` can be deleted directly under this request; moving it elsewhere is unnecessary. Release disposable worktrees through [their native owner](task-resource-lifecycle.md#worktrees-and-disposable-checkouts), never as ordinary directory trees.
5. Read back each deleted path's absence and preserve unrelated siblings. Continue after a candidate fails; report the exact inaccessible, active, retained or uncertain item. Remove an empty task directory only when its ownership is verified. Report directory counts and measured disk bytes when available; do not claim RAM savings from file deletion.

Finish with the requested scope, actual removed run directories/worktrees, naming defects and producer repairs, exact active/retained skips and remaining coverage limits. Do not create an automation or infer permission to delete application data from its directory name. The automatic [Ending resource audit](ending-resource-audit.md) uses the same indexed due-run pass alongside its bounded originating/recent-chat checks; a manual cleanup request uses the discovery scope above.

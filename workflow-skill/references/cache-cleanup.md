# Requested Cache cleanup

Use this workflow when the user requests Cache or `temp-*` cleanup. The request authorizes deletion of eligible temporary support within the selected scope. Complete independent safe cleanup without asking again; preserve exact active, recovery, shared and review/reuse resources.

## Select the requested scope

| User request | Discovery scope |
| --- | --- |
| One project, Cache or temporary directory | Only the named project's owners or exact selected directory. An unqualified “this project” means the current project. |
| All Codex projects | Use `list_projects` and current chats/worktrees to enumerate exact project roots and hosts; deduplicate roots and their artifact owners. Include projects outside the current workspace. |
| The whole computer | Enumerate accessible local volumes and discover Skill-generated `Cache/temp-*` directories and configured external task stores. Do not reduce this to the current workspace or only registered Codex projects. |

Do not expand a single-project request to other projects. Whole-computer scope covers accessible storage on this computer; remote hosts require their own requested scope. Report unavailable hosts, volumes, permissions or incomplete inventories rather than claiming exhaustive cleanup.

## Check exact runs and consumers

Before deletion, inspect native Codex project/chat status with `list_threads`, `wait_threads` or exact `read_thread` calls as needed. Map tests, builds, external jobs, workers and worktrees to their exact run roots and consumed resources. Protect only those resources still needed by live, recovery, shared or review/reuse consumers, including the current cleanup run. An active project/chat does not protect completed sibling runs; an open or idle chat alone proves neither use nor disposability.

Treat paused, failed, resuming, approval-waiting or unknown runs as protected only where actual recovery or active-use needs remain. If a candidate's consumers cannot be established, retain that candidate and report the gap; continue other eligible runs, including in the same project/chat. Do not stop active jobs, close user apps, interrupt chats or wait for the whole project to finish to release an independent completed run.

## Traverse and delete eligible temporary directories

1. For each selected project, inspect its known Cache owners and use `project_artifact_directory(project_root, create=False)` from [the path resolver](../scripts/task_artifact_paths.py) for its external task store. Current support uses `TaskArtifacts/p-<project-key>/temp-<task-key>-<run-id>/`; older external `t-<task-key>/` and project `Cache/temp-*` are compatibility/cleanup inputs only. New executions always follow the [external artifact policy](project-cache-artifact-policy.md).
2. Discover `temp-*` directories directly beneath Cache owners, including owned Cache folders nested within the requested scope. Whole-computer discovery also checks non-Codex project roots and configured external stores. Do not match arbitrary `temp-*` elsewhere, traverse symlinks/junctions/reparse points, or enter Codex-managed storage, system/virtual stores or unrelated application caches. Inaccessible branches stay pending.
3. Confirm the candidate is Skill-generated disposable support from a finished unit with no remaining consumer. Use project rules, producer/run history or ownership records; directory name, age, size or an idle chat alone is insufficient. Existing directories may be cleaned even when this chat did not create them. For continued work, verify selective copies of useful inputs into its newly allocated run before retiring the old dependency; never copy the entire scratch tree. Preserve source, canonical runtime/asset caches, memory vaults, requested outputs, review/reuse environments, shared resources, unsaved work and minimum recovery inputs. Missing retention metadata is not deletion permission.
4. Recheck exact run/resource activity, consumers and directory identity immediately before each deletion. Resolve and bounds-check the candidate against its selected Cache or external project owner; reject links anywhere in the tree. Use portable native filesystem operations and delete only the selected disposable directory, never its entire Cache, project or artifact base. For an existing resource ledger, use its owner/helper and honor its retention and release barriers. An eligible legacy `Cache/temp-*` can be deleted directly under this request; moving it elsewhere is unnecessary. Release disposable worktrees through [their native owner](task-resource-lifecycle.md#worktrees-and-disposable-checkouts), never as ordinary directory trees.
5. Read back each deleted path's absence and preserve unrelated siblings. Continue after a candidate fails; report the exact inaccessible, active, retained or uncertain item. Remove an empty task directory only when its ownership is verified. Report directory counts and measured disk bytes when available; do not claim RAM savings from file deletion.

Finish with the requested scope, actual removed run directories/worktrees, exact active/retained skips and remaining coverage limits. Do not create an automation or expand this into a computer-wide deletion of all caches. The automatic [Ending resource audit](ending-resource-audit.md) retains its bounded originating/recent-chat scope; a manual cleanup request uses the scope above.

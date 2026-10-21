---
name: workflow-skill
description: "Coordinate parallel work, Monitor Mode, bounded verification and resource cleanup. Use for requested Cache/temp-* cleanup of one project, all Codex projects or the whole computer; preserve exact active resources and user review/reuse."
---

# Workflow

Before any file write, apply the [external artifact policy](references/project-cache-artifact-policy.md). Allocate a fresh external `temp-<task-key>-<run-id>/` from its first write for each request or test/build/package/deploy work unit, including continued work in the same chat. Share its exact run owner with dependent tools and delegates. Maintained source, final deliverables and real runtime/assets keep their owners; inspect exact paths and the Git index before committing.

Apply [Task Analyze](../task-analyze-skill/SKILL.md) for correct names and the opening brief: result, qualitative difficulty, known models, branch roles and dependencies. Keep it proportional to the work; a simple task needs only a sentence. Follow its [action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests) through execution, recovery and the final response.

Follow [Task Analyze's final Skill report](../task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting): keep an internal record of exact Skills actually used, their steps or actions and reasons. Gather delegated branch use for one parent-visible final summary; ordinary progress updates need no repeated Skill list.

For every UI or visual presentation task, including websites, PDF reports, documents, and slide presentations, read the [shared readable UI rules](references/readable-ui.md). Apply them even without code changes and when another Skill owns rendering or export.

For image generation, edits, retries, or batches, follow [image generation and closure](references/image-generation.md): use the required browser entry, prepare downstream work while generation runs, move native downloads into their exact owner, and finish bounded cleanup without blocking independent jobs.

## Browser testing

For any browser-based test, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence. Keep task-created browser surfaces hidden unless the user asks to show them; retain user-opened and shared surfaces.

## Keep work moving

Start every ready independent branch promptly through concurrent tools or subagents with clear goals and disjoint write ownership. Serialize only genuine prerequisites, shared mutable owners and required authorization. Join a branch when its output is needed. For example, generate an image while a separate branch cleans confirmed disposable files; prepare output paths, layout inputs and QA criteria before the image arrives. Never delete an active job's inputs or backing resources.

Prefer events or completion notifications to polling. Give external jobs a time budget; use bounded checks with backoff while doing other ready work. If the budget expires or a client stays stale, record the exact job/target, last authoritative state and recovery action as pending, then continue independent work. The budget bounds polling for that step; it does not declare the whole task failed or excuse skipping useful implementation or recovery. Never duplicate a possibly accepted submission just because its UI is slow.

Ending is fully independent of its originating thread and has no join point in that thread. After app creation acknowledgement, the main turn ends immediately; never wait, poll, collect Ending results, resume the parent for recovery, or make the parent delete Ending. Ending reads its exact source thread when needed and owns its branch readbacks, recovery and mandatory self-deletion under [Project Memory](../project-memory-skill/SKILL.md#ending-conversation-cleanup). This exception applies to every wait, Monitor Mode and closeout policy.

A site's authoritative success receipt or acknowledgement completes the submission step and unblocks independent work. Submission accepted, backend completion verified, tab closed and scratch removed remain separate states. Make at most one immediate readback and one bounded final readback for an acknowledged action; stale UI or unavailable APIs leave verification pending instead of triggering an endless loop. Return to exact owned tabs during final cleanup and close those no longer needed. Actual output acceptance, byte verification and irreversible-action authorization still govern their real dependents.

## Monitor Mode

Use [Monitor Mode](references/monitor-mode.md) when the user asks to monitor another chat, or a long task needs continuing supervision and repeated verification to establish its final result. Keep the current chat as monitor and create authorized worker chats for independently owned modules in the same project. Work on the same module, function or shared mutable owner stays in this chat with subagents and coordinated writes. Duration alone does not justify a separate chat.

Check every five minutes, with earlier attention for completion or actionable failures. Compare progress with the user's scope, owning Skills, exact-project memory and current evidence. Stay quiet while work is on course; send brief steering only for a concrete deviation or blocker. Stop confirmed out-of-scope work through a supported control, or request a pause and verify acknowledgement when only messaging is available. Verify the agreed final result before closing supervision.

## Cleanup at every task transition

At the start of every new user request or distinct work unit, including unrelated work in the same chat, apply the [task-transition cleanup checkpoint](references/task-resource-lifecycle.md#task-transition-cleanup-checkpoint) before producing new scratch or starting another build/package/test. Reclaim completed predecessors' confirmed unused support immediately; do not wait for chat closure, Ending, a separate cleanup request, a disk-space threshold or a time-to-live. This is standing authorization, not an optional suggestion. Cleanup failure blocks only the affected resource, not independent new work.

Use the local [Cache cleanup helper](references/cache-cleanup.md#local-index-and-executable-checkpoints) at start, transition and finish. Each checkpoint also examines registered disposable runs from other tasks: after 24 hours without heartbeat or descendant changes, release them when fresh consumer checks pass. Own completed/obsolete runs have no age delay. Inspect project Cache naming violations too: direct child directories must be `temp-*` or `remote-*`; find and repair the producer, remove disposable violations, and resolve actual retained-resource ownership instead of disguising garbage by renaming it.

## Requested Cache cleanup

When the user asks to clean Cache, `temp-*`, all Codex projects, or the whole computer, follow [Cache cleanup](references/cache-cleanup.md). Match the requested scope, enumerate exact runs and consumers, then delete only confirmed disposable Skill-generated support. A running project or chat protects only resources it still uses; completed earlier runs may be cleaned immediately. An explicit cleanup request covers eligible legacy `Cache/temp-*` directly; no migration or routine confirmation is required.

## Git branch ownership

- Inspect the actual current local branch, configured upstream, index, dirty files and active Git/recovery operations before writes. Unless the user selects another target, keep task edits, commits, upstream merges and normal pushes on that current branch; tell the user its actual name and proceed without a routine confirmation. A branch named `master` follows this same current-branch rule. A repository default or merge-source mention never selects a different delivery branch.
- Switching branches, creating a delivery branch or publishing additional branches requires an explicit target in the user's request. “Merge master into my branch” updates the selected branch only. Do not invent or switch branches to avoid conflicts or a missing target. Detached HEAD leaves the intended delivery branch pending until it is specified.
- Resolve publication through the selected branch's existing configured upstream. Missing upstream is a delivery blocker, not permission to guess `origin/main`, borrow another branch's target or claim a local commit completed the request. Preserve the local commit and report its SHA and the exact missing target. A user explicitly requesting a local-only commit or no push keeps that exception.
- If the user explicitly requests delivery to multiple branches, preserve each branch's unrelated work and publish only those targets through their verified upstreams. Merge the latest upstream before each normal push, read back each remote ref, and return to the original checkout. Do not synchronize other branches by inference.

## Execute

Git delivery is one complete transaction. A request to commit, merge, restore or push includes authorization to normally push the task-owned commits on the selected branch to its existing configured upstream, unless the user explicitly requests a local-only commit or no push. A local commit is an intermediate state; continue through remote delivery in the same task.

For every Git-managed update, inspect the current branch, configured upstream, index and dirty files; preserve unrelated work; then fetch and merge the latest upstream before scoped changes. Complete the changes and necessary verification, stage only task-owned changes, and commit immediately. Before every push, fetch again and merge the latest configured upstream into the same branch, resolve conflicts without discarding either relevant intent, and rerun affected checks when integration changes the result. Then perform a normal push. If the remote advances and rejects the push, repeat fetch, merge, conflict resolution and affected verification, then retry the normal push while a useful authorized route remains. Use merge for upstream integration and preserve published history. Never guess a missing upstream, force-push or publish unrelated work or additional branches.

Declare Git delivery complete only after a fresh remote-ref readback matches local HEAD and all task-owned file changes are committed. Report the branch, upstream and delivered commit hash. A missing target, unavailable network or credentials, or an unresolved conflict leaves remote delivery pending: report the exact blocker, unpushed commit hashes and minimum recovery action, and distinguish committed locally from pushed remotely. Restore and verify every temporary integration stash in the same task, then drop only that exact consumed stash; preserve unrelated existing stashes and recoverable conflicting snapshots.

1. Identify the result, project and constraints. Apply [automatic project AI index](../management-skill/references/project-ai-index.md) at start/resume to discover or build the project's index and select focused context. Read exact project/module/file/symbol memory through [Project Memory](../project-memory-skill/SKILL.md); skip absent entries and keep cross-project references explicit.
2. Preview the branches, qualitative difficulty, known models and real dependencies through Task Analyze, then proceed without a routine approval pause.
3. Apply the ready-work policy above. Start independent branches together, prepare downstream work during external waits, and integrate outputs only at their actual join points.
4. Reconcile root `AGENTS.md` and the project index with established user intent and affected source structure before final verification and authorized Git delivery. Verify changed code or consequential results using [Verify](../verify-skill/SKILL.md); use the smallest real boundary without starting the whole project unless requested. Pass the scoped guidance evidence to Ending for its residual check; if Ending is unavailable, finish inline.
5. At each work unit's verified delivery, release its exact disposable scratch, test/build intermediates, idle surfaces and owned worktrees through [resource ownership](references/task-resource-lifecycle.md). A long-running chat or later work unit does not delay this cleanup. For continuation, allocate a fresh run and verify selective copies of useful inputs before retiring the old run. Preserve files and live environments needed for review, reuse or minimum recovery in their actual owner. Report result, cleanup and concrete ownership/API blockers, distinguishing source edits, installation and publication.
6. Apply Project Memory’s native-deletion preflight before creating a saved Ending; if the creating service has no verified deletion route, finish scoped memory/resource closure in the current chat without creating another conversation. After delivery and in-task verification, launch the authorized visible Ending for useful [Project Memory](../project-memory-skill/SKILL.md) work and the [resource audit](references/ending-resource-audit.md), then show the acknowledged link and immediately end the main turn. Ending alone joins its parallel branches, reads their records, resolves missing context by reading the origin thread, and deletes its own completed conversation under [Project Memory's cleanup rule](../project-memory-skill/SKILL.md#ending-conversation-cleanup). Workflow coordinates resources there; memory failure never blocks reclamation. Archival remains deletion pending and never brings the parent back into closeout.

## Boundaries

Preserve unrelated work. Perform reversible actions within the request; obtain authorization for actions outside it. Never message others without explicit authorization. Report only results supported by evidence.

Apply [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md) to all scripts, tests, and background work, including delegated and nested launches. Capture output without visible windows or focus changes; opening a terminal, browser, report, or app requires an explicit request to show it.

Use [resource ownership](references/task-resource-lifecycle.md) and the [external artifact policy](references/project-cache-artifact-policy.md) when creating temporary resources. Ordinary work needs no extra ledger; record exact handles/paths when cleanup spans tasks or consumers. Never sweep Codex-managed storage or affect active/shared/user-opened resources.

The user gives standing authorization to delete task-owned disposable local Cache/scratch, verified download duplicates, and cloud files generated by the task, including Google and ChatGPT files. After exact ownership, consumer checks and required output handoff, perform eligible cleanup directly without another permission question; follow the provider's normal recovery flow and read back the result. This does not authorize deleting formal originals, requested results, active/shared resources or unrelated user files. If a higher-priority tool rule requires action-time confirmation for an irreversible deletion, request only that required confirmation for the concrete batch; an already confirmed unchanged batch needs no repeat question. Preserve and report blocked targets without bypassing the control.

Ordinary task results update their source, outputs or project memory. Automatically maintain project root guidance and AI-index routes under [their global owner](../management-skill/references/project-ai-index.md); other Skill edits still follow the [authoring rules](../management-skill/SKILL.md#authoring-rules).

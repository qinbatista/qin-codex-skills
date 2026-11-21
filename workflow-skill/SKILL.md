---
name: workflow-skill
description: "Coordinate parallel work, Monitor Mode, bounded verification and resource cleanup. Use for requested Cache/temp-* cleanup of one project, all Codex projects or the whole computer; plan file disposal before work and clean each delivered unit immediately."
---

# Workflow

Before implementation or payload writes, make the [unit cleanup plan](references/project-cache-artifact-policy.md#plan-before-producing-files). Record purpose, deletion set, final destinations and any exact retained inputs with consumers and end conditions. Default to releasing all scratch. Avoid shared pools, convenience backups and speculative copies. Keep source, deliverables and native runtime or assets with their owners. Apply the [project Cache artifact policy](references/project-cache-artifact-policy.md) before writes.

Allocate fresh producer-owned `Cache/temp-<task-key>-<run-id>/` scratch from the first write of each request or test/build/package/deploy unit. A requested generator's required Cache is in scope. Keep receiving-project output and tests in their own project Cache. Write intermediates and test output directly to the new run, including for producers in `remote-*`. Reserve `Cache/remote-*` for exact files in a Git-tracked contract with a lasting consumer and verified synchronization route. Default uncertain output to `temp-*`.

Before payload writes, record the workspace baseline and producer runs. Share exact ownership with dependent tools and delegates. Track paths and handles for the [task leftover check](references/ending-resource-audit.md#check-and-reclaim-task-leftovers).

Apply [Task Analyze](../task-analyze-skill/SKILL.md) for naming, the opening brief and [action completion](../task-analyze-skill/SKILL.md#complete-action-requests) through verification and delivery. Track actual Skill use across branches for [one final report](../task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting).

Use the [shared readable UI rules](references/readable-ui.md) for all UI and visual presentation work, including websites, PDF reports, documents and slide presentations, even without code changes or when another Skill renders or exports.

For image generation, edits, retries or batches, follow [image generation and closure](references/image-generation.md) for browser entry, work during generation, download handoff and bounded cleanup.

## Long text and machine logs

Use [bounded text and log reading](references/text-and-log-reading.md) for long text, build/test output and errors. Start chronological logs at the last page, move back as needed and search specific terms with bounded context.

## Browser testing

For any browser-based test, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence. Keep task-created browser surfaces hidden unless the user asks to show them; retain user-opened and shared surfaces.

## Keep work moving

Start ready independent work through concurrent tools or authorized subagents with clear goals and disjoint writes. Serialize prerequisites, shared mutable owners and authorization. Prepare downstream work while jobs run and join when outputs are needed. Preserve active inputs and backing resources.

Prefer completion events. Use bounded checks with backoff while independent work proceeds. If a check budget expires or a client stays stale, record the job, latest authoritative state and next recovery action. Continue through service status, a supported wait or another viable recovery path. Check existing submissions before retrying. Apply Task Analyze's blocker rule once no useful authorized action remains.

An authoritative receipt proves submission. When submission is the endpoint, use at most one immediate and one bounded final readback. For backend completion, follow the job to its authoritative final state and verify its output. Gate dependents on their actual acceptance, byte verification and authorization requirements. Release unused owned tabs at final cleanup.

## Monitor Mode

Use [Monitor Mode](references/monitor-mode.md) for requested chat monitoring or work that needs ongoing supervision and repeated verification. Keep this chat as monitor. Create authorized workers only for independently owned modules in the same project. Shared modules, functions and mutable owners stay here with coordinated writes and authorized subagents.

Check every five minutes or earlier for completion or actionable failure. Compare progress with scope, Skills, exact-project memory and evidence. Send brief steering only for concrete deviations or blockers. Stop confirmed out-of-scope work through supported controls, or request a pause and verify acknowledgement if only messaging is available. Verify the agreed result before closing supervision.

## Cleanup at every task transition

Use the [Cache cleanup helper](references/cache-cleanup.md#local-index-and-executable-checkpoints) at start, [before every new request or work unit](references/task-resource-lifecycle.md#task-transition-cleanup-checkpoint), at delivery and at finish. Reclaim confirmed unused predecessors before new scratch, builds, packages or tests under standing authorization. An affected resource can remain pending while independent work continues.

Hand off requested final files to their real owner outside scratch. A local package is a deliverable when the user needs it locally. After each verified and reported result, immediately run `checkpoint --phase delivery` and read back absence. Release consumed packages, exports and intermediates through native owners. Preserve review/reuse resources with verified consumers, exact necessary active or recovery inputs, and explicit holds from the plan. Generic reuse, setup savings and backups are insufficient. Release holds through the owner after the user ends them.

At current-project startup and finish, read AI-index `cache/README.md` and optional `cache/owners.json`. After cleanup, run Management's `project_ai_index.py cache --project-root ROOT --apply` to replace the bounded ignored `cache/current.json` with current entries. Reference lookups skip cleanup and inventory writes.

Process explicit owners first, then completed or obsolete disposable runs and resumable deletions. Check remaining runs oldest heartbeat first. Abandoned runs require 48 hours without heartbeat or descendant changes and fresh consumer checks. Resume interrupted deletion only from its unchanged original proof. Resolve retention gaps and repair in-scope producers of obsolete entries.

For retries, use the [allocator's continuation command](references/project-cache-artifact-policy.md#separate-executions-and-continuation) with the exact previous run of the same task. Transfer only named inputs to a fresh run. Use the returned environment after verified removal of the predecessor.

After fresh consumer checks, the helper can unlink internal symlinks and closed FIFO/socket nodes without following them. Protect escaping links, reparse points, mounts, hard links and device nodes. Reclaim eligible isolated installations with ordinary internal links.

Run the leftover check across all tool-owned locations at inline closeout. Keep Codex chats, sessions and databases user-managed. Closeout creates no automatic Ending chat.

## Requested Cache cleanup

For requested Cache, `temp-*`, multi-project or whole-computer cleanup, follow [Cache cleanup](references/cache-cleanup.md). Enumerate exact runs and consumers within scope. Release confirmed disposable Skill-generated support, including eligible legacy `Cache/temp-*` directly under explicit cleanup authorization. Preserve resources with live consumers, including in chats with already completed runs.

For opted-in daily cleanup, check the date before project discovery and run the [multi-project sweep](references/cache-cleanup.md#daily-multi-project-sweep) on the first local task of the day. Continue after the sweep or an already-checked result. Report exact pending owners.

## Git branch ownership

- Follow explicit task and project branch, worktree, merge and publication rules before switching or editing. For an account-scoped audit, match each checkout's remote to the requested owner before changing refs or worktrees. Inspect read-only tasks in place.
- Otherwise use the actual `master` or `main` for both base and delivery, even from a different branch or detached HEAD. Resolve ambiguity with repo guidance, upstream config and remote symbolic `HEAD`. Confirm the exact upstream before fetching or pushing. Announce branch and upstream. Use the primary checkout when safe, or a worktree from the updated base.
- Preserve unfinished files, staged changes, existing branches, unique commits and active checkouts. Include only reviewed, completed task paths and commits. Resolve ambiguous refs before using them. If upstream is unavailable and primary is known, commit verified work wherever safe and report the pending delivery and SHA. Honor explicit hold, local-only and no-push scope.
- Close completed task branches in the same task. Integrate reviewed work under project policy, push and read back the result on the remote primary. Recheck each task tip, remove its clean worktree, delete the merged local and remote branches and prune their tracking refs without asking again. Verify absence in the worktree list, local refs and remote heads. Preserve active work and shared refs. Before retiring a release branch, verify its replacement with the publisher and consumers. Address branches and same-named tags by their full refs.

## Worktree isolation

- Before editing, compare planned paths, generated outputs and dependencies against dirty/staged paths and active owners. Check `git status`, `git diff --cached`, `git worktree list` and active Git operations. If overlap, switching or an independent checkout requires isolation, create one attached local `codex/<task>` branch and worktree from verified primary. Serialize ref and index writes.
- Consider tracked files, LFS, submodules and recompile/import costs. Use sparse checkout when dependencies allow. Materialize needed inputs only. Keep original caches with their native consumers and avoid copying untracked files, dependencies, builds or whole projects. Follow [worktree lifecycle](references/task-resource-lifecycle.md#worktrees-and-disposable-checkouts) and the owning Git or Codex service.
- Verify in the worktree. Refresh the primary upstream and rebase unpublished task commits when needed. Amend or squash only task-owned unpublished commits and recheck the tree. Correct published changes with a new commit or revert. Fast-forward primary in its own checkout as soon as work is verified. Reconcile overlap and recheck both sides' behavior. Publish through the primary upstream. Remove the clean worktree and local branch after fresh readback proves delivery. If landing is blocked by an active writer or conflict, preserve the exact committed recovery state.

## Linear local updates

Require linear incoming and outgoing commit ranges under the shared default, including other contributors' commits. Capture the accepted primary tip before fetching and run `git rev-list --min-parents=2 <accepted-tip>..<fetched-tip>` before integration. A fast-forward can import an existing merge. Before delivery, check `git rev-list --min-parents=2 <fetched-tip>..<candidate-tip>` against the freshly verified upstream. Require empty results and preserve the accepted base. If either range contains a merge, preserve both histories and reconcile the substantive commits and merge-only changes into a linear candidate. Apply the published-history repair below when the incoming commits are already shared.

Keep every ordinary update on one linear history. Fetch the actual configured upstream; fast-forward upstream-only updates with `git merge --no-autostash --ff-only <fetched-tip>`. For divergence, compare both sides and replay only verified unpublished local commits with `git -c rebase.updateRefs=false rebase --no-autostash --no-rebase-merges <fetched-tip>`. Automatic pull workers use that same policy for compatible clean divergence when publication identity is established; conflicts, dirty/index work, active operations, local merge-only changes or unknown publication state remain recoverable pending work. Never create a merge commit or use `--rebase-merges`, `--no-ff`, or `pull --no-rebase`, and never make a worker's policy depend on test-output variables. A local pull does not authorize an automatic commit or remote push.

Set and read back effective `pull.rebase=true`, `branch.<current>.rebase=true`, `pull.ff=true`, `merge.ff=only`, `rebase.rebaseMerges=false` and `rebase.updateRefs=false` in the managed checkout. Replace an inherited `pull.ff=only` that blocks divergence replay. Pass `--no-autostash` in automation. Preserve staged, unstaged, untracked, peer and recovery work.

An explicit request to flatten published merge history authorizes that exact repair through delivery. Preserve substantive side commits, merge-only and concurrent changes, final bytes, unrelated dirty work and the original tip through native Git recovery. Publish only the selected branch with an exact-old-tip transaction or specifically authorized lease-protected replacement. Preserve receiver protections. Read back local, tracking and fresh remote tips and check all reachable merges.

When pulling an explicitly flattened upstream, prove the old base, replacement base and substantive content with the repair's exact old/new mapping or independently verified equivalent commit trees. Replay only newer local commits with `rebase --no-autostash --no-rebase-merges --onto <replacement-base> <old-base>`. Retain exact recovery inputs and verify resulting files and upstream. Leave uncertain rewrites pending. Never reset broadly, discard local work or force-push as ordinary recovery.

## Resolve integration conflicts

Recover stopped merges, rebases and stash restores in this task. Inspect status, unmerged stages and common base. Compare both changes, current requirements, callers and tests. Preserve compatible behavior and apply scoped explicit replacements. Stage exact resolutions, continue the pending operation or restore the original index state, and verify combined behavior before delivery.

For rejected pushes, transport failures or failed readbacks, query the remote to see if delivery landed. Fetch and reconcile new upstream work, rerun affected checks and retry while authorized. Escalate only unresolved material ambiguity, access or authorization dependencies. Preserve both inputs and the exact recovery state and continue independent work.

## Execute

At start/resume, run [the AI-index gate](../management-skill/references/project-ai-index.md) for the current project before discovery. Obtain first-bootstrap consent when needed. Reference lookups skip their gate and maintenance. Recall exact project/module/file/symbol context through [Project Memory](../project-memory-skill/SKILL.md) and skip absent entries.

Git changes include integration, verification, scoped commit and normally a push through the configured upstream under standing authorization. Respect project rules and explicit read-only, hold, local-only and no-push scope.

Fetch and integrate the configured delivery upstream before edits, each commit and each push. In a worktree, refresh that same upstream and integrate the latest primary base before committing. Apply [linear updates](#linear-local-updates) to manual pulls, background source checks, Skill updates and delivery. If integration needs a clean tree, set aside only task-owned paths and restore their index state. Reconcile both intents and rerun affected checks after integration. [Resolve conflicts](#resolve-integration-conflicts) in the same task.

Reconcile root `AGENTS.md` and index scope before final verification and delivery. Use [Verify](../verify-skill/SKILL.md) at the smallest real boundary and start the whole project only if requested. Inspect exact paths and Git index. Stage only verified task changes and commit promptly. Push normally to the verified ref and keep task branches local.

Verify committed delivery and match local delivery HEAD to a fresh remote readback unless local-only. Release integrated task branches and worktrees. Restore and verify any temporary integration stash, then drop only that exact consumed stash. Preserve unrelated stashes, branches and live checkouts. Report branch, upstream, commit and any exact pending SHA, blocker and recovery state.

Release exact disposable support at each verified delivery through [resource ownership](references/task-resource-lifecycle.md). Finish the residual guidance check and scoped [inline closure](../project-memory-skill/SKILL.md#inline-guidance-memory-and-resource-closure). Report results, cleanup and concrete blockers, distinguishing source, installation and publication.

## Boundaries

Preserve unrelated work. Perform reversible actions in scope. Obtain authorization for actions outside scope or messages to others. Report evidenced results.

Use [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md) for every script, test and background command, including delegated or nested launches. Capture output without visible windows or focus changes. Open a terminal, browser, report or app only on request to show it.

Use [resource ownership](references/task-resource-lifecycle.md) for temporary resources. Track exact handles and paths when cleanup spans tasks or consumers. Preserve Codex-managed storage and active, shared and user-opened resources.

Standing authorization covers disposable task Cache, verified download duplicates and task-generated cloud files, including Google and ChatGPT files. Check exact ownership and consumers, hand off required outputs, use the provider's normal recovery flow and read back cleanup. Preserve originals, deliverables, active/shared resources and unrelated files. If a higher-priority tool rule requires action-time confirmation for irreversible deletion, ask only for that batch. Reuse unchanged confirmation and report blocked targets.

Keep results with their source, output or memory owner. Maintain current-project root guidance and index through Management. Follow its [authoring rules](../management-skill/SKILL.md#authoring-rules) for Skill edits.

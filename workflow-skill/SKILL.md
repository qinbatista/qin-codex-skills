---
name: workflow-skill
description: "Coordinate parallel work, Monitor Mode for long tasks or other chats, bounded verification and resource cleanup while preserving scope, active work and user review."
---

# Workflow

Before any file write, apply the [external artifact policy](references/project-cache-artifact-policy.md). Resolve task support outside project directories and Codex storage from its first write, including browser/helper output and child-tool caches. Share the resolved project/task owner with delegates. Maintained source, final deliverables and real runtime/assets keep their owners; inspect exact paths and the Git index before committing.

Apply [Task Analyze](../task-analyze-skill/SKILL.md) for correct names and the opening brief: result, qualitative difficulty, known models, branch roles and dependencies. Keep it proportional to the work; a simple task needs only a sentence. Follow its [action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests) through execution, recovery and the final response.

Follow [Task Analyze's final Skill report](../task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting): keep an internal record of exact Skills actually used, their steps or actions and reasons. Gather delegated branch use for one parent-visible final summary; ordinary progress updates need no repeated Skill list.

For every UI or visual presentation task, including websites, PDF reports, documents, and slide presentations, read the [shared readable UI rules](references/readable-ui.md). Apply them even without code changes and when another Skill owns rendering or export.

For any browser-based test, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence.

For image generation, edits, retries, or batches, follow [image generation and closure](references/image-generation.md): use the required browser entry, prepare downstream work while generation runs, move native downloads into their exact owner, and finish bounded cleanup without blocking independent jobs.

## Keep work moving

Start every ready independent branch promptly through concurrent tools or subagents with clear goals and disjoint write ownership. Serialize only genuine prerequisites, shared mutable owners and required authorization. Join a branch when its output is needed. For example, generate an image while a separate branch cleans confirmed disposable files; prepare output paths, layout inputs and QA criteria before the image arrives. Never delete an active job's inputs or backing resources.

Prefer events or completion notifications to polling. Give external jobs a time budget; use bounded checks with backoff while doing other ready work. If the budget expires or a client stays stale, record the exact job/target, last authoritative state and recovery action as pending, then continue independent work. The budget bounds polling for that step; it does not declare the whole task failed or excuse skipping useful implementation or recovery. Never duplicate a possibly accepted submission just because its UI is slow.

A site's authoritative success receipt or acknowledgement completes the submission step and unblocks independent work. Submission accepted, backend completion verified, tab closed and scratch removed remain separate states. Make at most one immediate readback and one bounded final readback for an acknowledged action; stale UI or unavailable APIs leave verification pending instead of triggering an endless loop. Return to exact owned tabs during final cleanup and close those no longer needed. Actual output acceptance, byte verification and irreversible-action authorization still govern their real dependents.

## Monitor Mode

Use [Monitor Mode](references/monitor-mode.md) when the user asks to monitor another chat, or a long task needs continuing supervision and repeated verification to establish its final result. Keep the current chat as monitor and create authorized worker chats for independently owned modules in the same project. Work on the same module, function or shared mutable owner stays in this chat with subagents and coordinated writes. Duration alone does not justify a separate chat.

Check every five minutes, with earlier attention for completion or actionable failures. Compare progress with the user's scope, owning Skills, exact-project memory and current evidence. Stay quiet while work is on course; send brief steering only for a concrete deviation or blocker. Stop confirmed out-of-scope work through a supported control, or request a pause and verify acknowledgement when only messaging is available. Verify the agreed final result before closing supervision.

## Execute

For every Git-managed merge or restore task, inspect the current branch and its configured upstream, preserve unrelated dirty work, then fetch and merge upstream before scoped changes. After necessary verification, immediately commit all task-owned merged or restored changes; do not defer the commit or leave them only local. Fetch again, rebase only unpublished local commits onto that upstream, make the authorized normal push, and verify the remote hash. The user's standing request to merge or restore work and leave no task changes local authorizes their normal push. Never guess a missing upstream, force-push, rewrite published history, or publish outside the request. Restore and verify every temporary integration stash in the same task, then drop only that consumed stash; never leave accumulating stashes. Preserve unrelated existing stashes.

1. Identify the result, project, constraints, and useful context. Read relevant skills and exact project/module/file/symbol memory through [Project Memory](../project-memory-skill/SKILL.md), including architecture only when needed. Skip absent entries. Keep cross-project references explicit and separate from authoritative project facts.
2. Preview the branches, qualitative difficulty, known models and real dependencies through Task Analyze, then proceed without a routine approval pause.
3. Apply the ready-work policy above. Start independent branches together, prepare downstream work during external waits, and integrate outputs only at their actual join points.
4. Verify changed code or consequential results using [Verify](../verify-skill/SKILL.md). Use one real check at the smallest relevant boundary; do not start or compile the whole project unless requested.
5. Verify requested results and their references in the declared durable owner through a fresh reader, then release exact disposable scratch, test/build intermediates and idle task-opened surfaces. Preserve files and live environments needed for user review or reuse; establish their output/resource owner before clearing backing scratch. On pause or failure, keep minimum recovery state and remove independent disposable work. Follow [resource ownership](references/task-resource-lifecycle.md). Report result, cleanup and concrete ownership/API blockers, distinguishing source edits, installation and publication.
6. After completion, use the authorized visible Ending for useful [Project Memory](../project-memory-skill/SKILL.md) work and the [resource audit](references/ending-resource-audit.md) in parallel. Workflow owns global resource coordination across the originating and recent completed tasks. Follow specific owners' cleanup first, then finish their missed cleanup through available owner tools. Memory failure never blocks reclamation; Ending never gates or re-verifies the main result.

## Boundaries

Preserve unrelated work. Perform reversible actions within the request; obtain authorization for actions outside it. Never message others without explicit authorization. Report only results supported by evidence.

Apply [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md) to all scripts, tests, and background work, including delegated and nested launches. Capture output without visible windows or focus changes; opening a terminal, browser, report, or app requires an explicit request to show it.

Use [resource ownership](references/task-resource-lifecycle.md) and the [external artifact policy](references/project-cache-artifact-policy.md) when creating temporary resources. Ordinary work needs no extra ledger; record exact handles/paths when cleanup spans tasks or consumers. Never sweep Codex-managed storage or affect active/shared/user-opened resources.

Ordinary task results update their owning source, outputs, or project memory. They do not trigger Skill edits; use the [authoring rules](../management-skill/SKILL.md#authoring-rules) only for an authorized durable workflow change or reusable defect repair.

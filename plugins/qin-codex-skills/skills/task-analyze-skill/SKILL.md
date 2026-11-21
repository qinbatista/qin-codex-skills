---
name: task-analyze-skill
description: "Define the final result and acceptance criteria, complete and verify authorized work in the active task, and manage the project AI index, chat names, and final Skill and memory reporting."
---

# Task Analyze

Read the request and [matching Qin Skills](references/global-skill-routing.md). Apply required startup and source-owner gates before project discovery or scoped memory recall.

Run [automatic project AI index](../management-skill/references/project-ai-index.md) at start/resume and finish for the current project only. Reference lookups skip its gate and maintenance. Only an explicit change of main project changes the scope. Ask for consent only before first bootstrap. Repair or expand existing indexes automatically within editable scope. For every project change, update and read back related index guidance or metadata before delivery. Reconcile concise root `AGENTS.md` when needed and check for remaining guidance changes in this chat.

When inspection reports `compression.status: due`, follow [AI Index Compression](../management-skill/references/project-ai-index.md#ai-index-compression), including exact-owner Obsidian review. Recheck after edits and before delivery. In explicit read-only scope, report flagged files only.

## Complete action requests

State the concrete final result, what will prove it, and any required delivery before detailed execution. Say whether it is feasible given the known prerequisites. Include steps, qualitative difficulty, known models and real dependencies. Use one sentence for simple tasks. Name each parallel branch and where it joins. Say "inherited" or "model ID not exposed" when appropriate.

For repeatable tests, diagnostics or multi-step work with stable inputs and checkable results, plan a local command and acceptance check using [Optimization's local execution guidance](../optimization-skill/SKILL.md#run-repeatable-work-locally).

An action request authorizes its necessary in-scope steps. Carry out every technically viable step within that authority. Use evidence and reasonable reversible assumptions to resolve routine choices without asking. Ask only for indispensable input, a decision only the user can make, or required authorization. Ask for the exact dependency once and continue independent work while waiting.

After a failure, diagnose the cause, repair it within scope, and retry the affected step or use another authorized approach. Use [Workflow's ready-work policy](../workflow-skill/SKILL.md#keep-work-moving) for external dependencies. Take the next useful action after failed attempts, unverified outcomes and expired check budgets. Share verified milestones and material changes. Never use an interim update to list unfinished work or hand back a step you can perform.

Before ending, check every requested outcome against actual evidence, including verification and delivery. Continue on every unmet requirement that still has a viable authorized path. End after verified completion, a user stop, or when relevant attempts or authoritative evidence show no further useful authorized work. Lead with verified results. State a blocker's exact cause and minimum external change needed. Keep the acceptance criteria unless the user changes them. Report only supported results.

## Mandatory visible Skill reporting

Record each exact Skill name actually used, the step or action and the reason in task context. Count Skills you read and applied. Delegated branches return the same details internally. Give one combined inventory in the final response, including partial, failed or paused outcomes. Identify planned but unused, missing or unreadable Skills separately. If none applied, report `Skills: none` and why. Check for omissions and report outward actions and results without private chain-of-thought.

In the same final response, include **Memory used**. For each distinct entry that informed work, give project → module → file → function or symbol as available, the recall identifier and the decision or action it supported. Preserve this record across compaction and authorized branches under [Project Memory's evidence rules](../project-memory-skill/references/project-knowledge.md#report-memory-used). If none informed work, report `Memory used: none` and the reason.

## Correct task names

Automatic naming is available once per chat. A creation title, user-chosen title or confirmed earlier rename uses that allowance. Inspect the exact chat's native title, creation context and history. Rely on its creation or rename receipt and readback. Preserve the current title unless first naming is demonstrably pending.

Use the shortest clear noun phrase for the main module, system, component or file, usually one to four words, such as `WeatherManager`, `Pantone Helper` or `BOM System`. Prefer exact identifiers. Add a qualifier only to distinguish the target. Omit actions, status, steps and request descriptions.

When first naming is pending and the target is clear, use the title tool and read back the result. Keep the first confirmed thread ID and title only in this chat's native receipt/history and carry that state across compaction. Read an uncertain result before retrying. Change a locked title only when the user explicitly requests a rename of this exact chat. Keep the original first-name record in that case. Report unavailable title control.

Resolve unambiguous spelling errors in function, feature or task names from authoritative source or context. Use the verified name in titles, plans, updates, labels and results. Clarify only ambiguous targets. Preserve literal quotations, data, proper names and exact identifiers. Show original spelling only for an exact reference or diagnostic.

## Carry out the task

Run [Workflow's cleanup checkpoint](../workflow-skill/references/task-resource-lifecycle.md#task-transition-cleanup-checkpoint) before each request or work unit, at delivery and finish. Reclaim confirmed disposable completed or obsolete support. Check registered abandoned runs and repair in-scope Cache naming violations.

Before implementation, make [Workflow's unit cleanup plan](../workflow-skill/references/project-cache-artifact-policy.md#plan-before-producing-files). Keep support in project Cache from its first write under the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md), including delegated output and tool caches. Release disposable support immediately after each verified and reported result.

For Git changes, follow [Workflow's branch ownership](../workflow-skill/SKILL.md#git-branch-ownership) at start/resume and its [delivery transaction](../workflow-skill/SKILL.md#execute) after verification. Announce the branch and upstream. Honor explicit read-only, hold, local-only and no-push scope.

Start independent work promptly and join it only when needed. Use [Monitor Mode](../workflow-skill/SKILL.md#monitor-mode) for supervision or repeated verification, with worker selection by module ownership and authorization.

[Verify](../verify-skill/SKILL.md) consequential changes here at the smallest real boundary. For every identifiable project task, including questions and investigations, complete [inline project guidance, memory and resource closure](../project-memory-skill/SKILL.md#inline-guidance-memory-and-resource-closure) in this chat. Honor explicit read-only, no-delete and hold limits and first-index consent. Read back each outcome independently and record actual skips or pending causes. Preserve active work and user review/reuse.

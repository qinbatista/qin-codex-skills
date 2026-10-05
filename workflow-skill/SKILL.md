---
name: workflow-skill
description: "Coordinate tasks, in-task verification, and global resource cleanup; audit completed-task leftovers at Ending while preserving active work, user review and reuse."
---

# Workflow

Before any file write, apply the [Cache policy](references/project-cache-artifact-policy.md). Every temporary file, including screenshots, JSON receipts, logs, and test output, belongs only in the resolved workspace's ignored `Cache/temp-<task>/`, from its first write. This applies to direct, delegated, browser, and helper work. Before staging or committing, inspect the exact paths and Git index; temporary files never enter Git.

Before detailed execution, briefly explain the requested result and the main implementation steps in plain language. Then follow those steps, incorporating any user correction or interruption. Keep the explanation proportional to the work; a simple task needs only a sentence.

For every UI or visual presentation task, including websites, PDF reports, documents, and slide presentations, read the [shared readable UI rules](references/readable-ui.md). Apply them even without code changes and when another Skill owns rendering or export.

For any browser-based test, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence.

For image generation, edits, retries, or batches, follow [image generation and closure](references/image-generation.md): use the required browser entry, move native downloads immediately into their exact resource owner, verify synchronization, and finish account cleanup and owned-tab closure before the next job.

## Execute

1. Identify the result, project, constraints, and useful context. Read relevant skills and exact project/module/file/symbol memory through [Project Memory](../project-memory-skill/SKILL.md), including architecture only when needed. Skip absent entries. Keep cross-project references explicit and separate from authoritative project facts.
2. State a short implementation outline before detailed work. Name the meaningful steps and dependencies, then proceed without a routine approval pause. Explain material changes to the outline as they arise.
3. Execute in dependency order. If independent work benefits from collaboration, give it a clear goal, relevant context, and disjoint write ownership; integrate the outputs in the active task.
4. Verify changed code or consequential results using [Verify](../verify-skill/SKILL.md). Use one real check at the smallest relevant boundary; do not start or compile the whole project unless requested.
5. Verify requested results and their references in the declared durable owner through a fresh reader, then release exact disposable scratch, test/build intermediates and idle task-opened surfaces. Preserve files and live environments needed for user review or reuse; establish their output/resource owner before clearing backing scratch. On pause or failure, keep minimum recovery state and remove independent disposable work. Follow [resource ownership](references/task-resource-lifecycle.md). Report result, cleanup and concrete ownership/API blockers, distinguishing source edits, installation and publication.
6. After completion, use the authorized visible Ending for useful [Project Memory](../project-memory-skill/SKILL.md) work and the [resource audit](references/ending-resource-audit.md) in parallel. Workflow owns global resource coordination across the originating and recent completed tasks. Follow specific owners' cleanup first, then finish their missed cleanup through available owner tools. Memory failure never blocks reclamation; Ending never gates or re-verifies the main result.

## Boundaries

Preserve unrelated work. Perform reversible actions within the request; obtain authorization for actions outside it. Never message others without explicit authorization. Report only results supported by evidence.

Apply [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md) to all scripts, tests, and background work, including delegated and nested launches. Capture output without visible windows or focus changes; opening a terminal, browser, report, or app requires an explicit request to show it.

Use [resource ownership](references/task-resource-lifecycle.md) and the [Cache policy](references/project-cache-artifact-policy.md) when creating temporary resources. Ordinary work needs no extra ledger; record exact handles/paths when cleanup spans tasks or consumers. Never sweep Codex-managed storage or affect active/shared/user-opened resources.

Ordinary task results update their owning source, outputs, or project memory. They do not trigger Skill edits; use the [authoring rules](../management-skill/SKILL.md#authoring-rules) only for an authorized durable workflow change or reusable defect repair.

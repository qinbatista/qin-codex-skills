---
name: task-analyze-skill
description: "Explain the goal, difficulty, known models and parallel branches, then keep ready work moving with focused verification."
---

# Task Analyze

Read the request, applicable skills, and relevant existing project memory. Identify the intended result and constraints without importing another project's facts.

## Correct task names

Resolve unambiguous spelling errors in user-supplied function, feature or task names from the owning source or authoritative context before naming the task. Use the verified correct name in titles, plans, progress, labels and results; do not echo the typo or a before/after mapping. Clarify only if the intended name is ambiguous. Preserve literal quotations, data, proper names and exact existing identifiers; show the original spelling only when an exact source reference or diagnostic requires it.

## Carry out the task

Before any file write, resolve its owner under the [Cache policy](../workflow-skill/references/project-cache-artifact-policy.md). Temporary files belong only in the workspace's ignored `Cache/temp-<task>/` from their first write, including delegated work. Inspect exact paths and the Git index before staging or committing; temporary files never enter Git.

Before detailed execution, briefly tell the user the result, qualitative difficulty, actual known model assignments, and implementation steps. Say "inherited" or "model ID not exposed" when that is all the available evidence; never invent a model name. Use one sentence for simple work; for multiple branches, name each subtask, its assignee/model, what runs in parallel, and the actual join dependencies. Keep this preview concise and update material changes.

Then follow [Workflow's ready-work policy](../workflow-skill/SKILL.md#keep-work-moving): start independent branches promptly and wait only where their outputs are needed. The user can interrupt or adjust the direction. Ask only when a missing decision materially affects the result or an action requires authorization; continue independent work where possible. Explain a material change in approach before carrying it out.

Verify consequential changes in the active task at the smallest relevant boundary, following [Verify](../verify-skill/SKILL.md). Report the result, evidence, and limits. Use [Project Memory](../project-memory-skill/SKILL.md) for scoped recall and useful durable updates; the authorized Ending runs memory work alongside [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md), preserving active work and user review/reuse.

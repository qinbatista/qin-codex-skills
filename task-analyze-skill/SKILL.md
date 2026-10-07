---
name: task-analyze-skill
description: "Track Skill use during work and summarize exact names, steps and reasons once at completion; explain goals and deliver action requests with recovery and verification."
---

# Task Analyze

Read the request, applicable skills, and relevant existing project memory. Identify the intended result and constraints without importing another project's facts.

## Mandatory visible Skill reporting

Keep a concise internal record as work proceeds: each exact Skill name actually used, the task step or action where it was applied, and the reason or purpose for using it. Read and follow a Skill before recording it as applied; a catalog entry, plan or name alone does not prove use. Collect the same actual-use details from delegated branches. This working record needs no separate per-task file.

Do not repeat Skill inventories at startup, resumed turns, analysis, task decomposition, execution, verification, deployment, cleanup or routine progress updates. Progress messages report work, evidence and next steps without a mandatory Skill list. Branches return their use records internally to the parent; the parent reports them with its own use once at the end.

In one final response, including partial, failed or paused outcomes, summarize all Skills actually used across the task and branches. Give each exact name, the step or action it supported, and a short reason or concrete contribution. Identify planned but unused, missing or unreadable Skills separately without claiming activation. If no Skill applied, say `Skills: none` and why. Correct omissions before completion. Report outward actions and results, never private chain-of-thought.

## Complete action requests

Treat an action request as authorization to carry out its intended work within scope. Deliver the requested change or artifact; a plan, diagnosis, list of problems, or "I tried and failed" alone does not fulfill it. Keep working while a useful authorized route remains.

When an attempt fails, inspect the cause, repair what is within scope, retry the affected step, or use a suitable available alternative. Complete independent work while a dependency is blocked. A failed command, test, unavailable verification tool, or polling budget does not by itself justify abandoning implementation. Bound repeated checks against unchanged external state; do not use a fixed retry count as a reason to stop work that can still progress.

Stop the affected work only for a concrete blocker that cannot be resolved through reasonable available actions within scope, such as confirmed missing network access, credentials, required input or authorization, an unavailable required runtime, or an impossible requirement. Establish the blocker through relevant attempts or authoritative evidence, explain its observed cause and what was attempted, and identify the minimum external change needed. Never bypass permissions, weaken acceptance, or invent success to avoid reporting a blocker.

Lead the final response with what was actually delivered and its verification. Distinguish implementation, testing, deployment and publication. A blocked check does not erase completed work: "Updated the function; runtime verification is blocked because the required service is unreachable" accurately reports both states. If no requested result is achievable, give the specific evidenced reason after exhausting useful routes; do not substitute a generic failure reply or a promise to try later.

## Correct task names

Resolve unambiguous spelling errors in user-supplied function, feature or task names from the owning source or authoritative context before naming the task. Use the verified correct name in titles, plans, progress, labels and results; do not echo the typo or a before/after mapping. Clarify only if the intended name is ambiguous. Preserve literal quotations, data, proper names and exact existing identifiers; show the original spelling only when an exact source reference or diagnostic requires it.

## Carry out the task

Before any file write, resolve its owner under the [Cache policy](../workflow-skill/references/project-cache-artifact-policy.md). Temporary files belong only in the workspace's ignored `Cache/temp-<task>/` from their first write, including delegated work. Inspect exact paths and the Git index before staging or committing; temporary files never enter Git.

Before detailed execution, briefly tell the user the result, qualitative difficulty, actual known model assignments, and implementation steps. Say "inherited" or "model ID not exposed" when that is all the available evidence; never invent a model name. Use one sentence for simple work; for multiple branches, name each subtask, its assignee/model, what runs in parallel, and the actual join dependencies. Keep this preview concise and update material changes.

Then follow [Workflow's ready-work policy](../workflow-skill/SKILL.md#keep-work-moving): start independent branches promptly and wait only where their outputs are needed. The user can interrupt or adjust the direction. Ask only when a missing decision materially affects the result or an action requires authorization; continue independent work where possible. Explain a material change in approach before carrying it out.

Verify consequential changes in the active task at the smallest relevant boundary, following [Verify](../verify-skill/SKILL.md). Report the result, evidence, and limits. Use [Project Memory](../project-memory-skill/SKILL.md) for scoped recall and useful durable updates; the authorized Ending runs memory work alongside [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md), preserving active work and user review/reuse.

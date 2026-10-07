---
name: task-analyze-skill
description: "Report exact Skill names and purposes at startup, throughout work and completion; explain goals and branches, then deliver action requests with recovery and verification."
---

# Task Analyze

Read the request, applicable skills, and relevant existing project memory. Identify the intended result and constraints without importing another project's facts.

## Mandatory visible Skill reporting

At every task startup and resumed turn, before the first tool call, tell the user the exact Skill names you plan to use and one short purpose for each. This applies even to simple tasks. Announce a newly selected Skill before reading or applying it; then actually read and follow its instructions.

Every user-facing progress update must include the exact names and short purposes of the Skills preparing or doing that work. Repeat this at analysis, task decomposition, pre-execution, execution, verification, deployment and cleanup transitions, even when the selection is unchanged. Use a compact line in the user's language, such as `Skills in use: workflow-skill — coordinate branches; verify-skill — check the output`. State planned versus already applied use accurately; a catalog listing, intention or name alone does not prove a Skill was applied. Report only outward actions and results, never private chain-of-thought.

Carry this rule into delegated goals. Each branch reports its own selection and actual use; the parent includes branch Skill names and purposes in visible updates and collects actual use for the final response. Internal messages alone do not fulfill visible reporting.

Every final response, including partial, failed or paused outcomes, must list all Skills actually used across the task and its branches, with a short description of what each did. Identify planned but unused, missing or unreadable Skills separately without claiming activation. If no Skill is applicable, explicitly say `Skills: none` with a short reason. If a disclosure was omitted, correct it before the next action or completion. Brevity and unchanged selection never waive this mandatory reporting.

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

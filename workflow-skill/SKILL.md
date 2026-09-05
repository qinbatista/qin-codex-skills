---
name: workflow-skill
description: "Coordinate tasks with clear goals, relevant skills, safe parallel work, and verification before completion."
---

# Workflow

The user's selected model understands the request, reads relevant skills and available project memory, and defines each task's goal and acceptance. Keep that model and reasoning effort for work governed by those skills. Adaptive routing is for independent work without applicable skill constraints; [Task Analyze](../task-analyze-skill/SKILL.md) owns that policy.

For every UI or visual presentation task, including websites, PDF reports, documents, and slide presentations, read the [shared readable UI rules](references/readable-ui.md). Apply them even without code changes and when another Skill owns rendering or export.

## Execute

1. Identify the requested result, project, constraints, and useful context. Show score/band, selected model/effort, route and identity evidence. Memory is optional: skip missing files and never substitute another project's records.
2. Execute simple work directly. Plan when dependencies or uncertainty warrant it. Delegate independent branches with explicit goals, inputs, outputs, ownership, and stop conditions; keep shared writes and output dependencies ordered. Show each delegated goal, score, pair and dependencies, then its actual result status.
3. Give workers only relevant skills and memory. A script inside a skill-governed code or UI task retains the parent's model constraint; a mechanical tool call needs no model.
4. Integrate outputs and verify the actual result inside this task using [Verify](../verify-skill/SKILL.md). Skip verification for a simple value-only change unless requested. Use the smallest convincing check; do not start or compile the whole project unless requested.
5. Report the result and evidence. Distinguish source edits, installation, and publication. The root owns completion; a child's readiness is only an input.
6. If useful durable information changed, finish with [project memory](../project-memory-skill/SKILL.md). Ending only summarizes and writes memory with the user's selected model and effort. For the user-authorized Ending lifecycle, create one separate visible projectless task and show its link and memory readback. It does not verify, repair, benchmark or reroute. Explicitly skip when no useful memory or configured store exists; missing launch capability is pending, never silent inline completion.

## Boundaries

Preserve unrelated work. Perform reversible actions within the request; obtain authorization for actions outside it. Never message others without explicit authorization. Only claim model identity or performance backed by evidence.

Apply [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md) to all scripts, tests, and background work, including delegated and nested launches. Capture output without visible windows or focus changes; opening a terminal, browser, report, or app requires an explicit request to show it.

Use [parallel ownership](references/parallel-session-orchestration.md) when delegating and [resource ownership](references/task-resource-lifecycle.md) and the [Cache policy](references/project-cache-artifact-policy.md) when creating temporary resources. These helpers support work; they are not mandatory receipt ceremonies.

---
name: workflow-skill
description: "Coordinate tasks with clear goals, relevant skills, safe parallel work, and verification before completion."
---

# Workflow

The user's selected model understands the request, reads relevant skills and available project memory, and defines each task's goal and acceptance. Keep that model and reasoning effort for work governed by those skills. Adaptive routing is for independent work without applicable skill constraints; [Task Analyze](../task-analyze-skill/SKILL.md) owns that policy.

For every UI or visual presentation task, including websites, PDF reports, documents, and slide presentations, read the [shared readable UI rules](references/readable-ui.md). Apply them even without code changes and when another Skill owns rendering or export.

For any browser-based test, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence.

## Execute

1. Identify the requested result, project, constraints, and useful context. Show score/band, selected model/effort, route and identity evidence. Ensure the Obsidian vault through [Project Memory](../project-memory-skill/SKILL.md), then read exact-project memory. Skip an absent matching note and never substitute another project's records.
2. Execute simple work directly. Plan when dependencies or uncertainty warrant it. Delegate independent branches with explicit goals, inputs, outputs, ownership, and stop conditions; keep shared writes and output dependencies ordered. Show each delegated goal, score, pair and dependencies, then its actual result status.
3. Give workers only relevant skills and memory. A script inside a skill-governed code or UI task retains the parent's model constraint; a mechanical tool call needs no model.
4. Integrate outputs and verify changed code or consequential results inside this task using [Verify](../verify-skill/SKILL.md). Use one real check at the smallest relevant boundary; do not start or compile the whole project unless requested.
5. Close and remove exact task-owned temporary surfaces and scratch after final readback unless review, debugging, or a downstream consumer still needs them. Revisit clearly superseded temporary previews on a later related task. Keep retained `Cache/remote-*` content. Then report the result and evidence, distinguishing source edits, installation, and publication. The root owns completion; a child's readiness is only an input.
6. If useful durable information changed, use [project memory](../project-memory-skill/SKILL.md) after the main task is complete. Ending writes only to the configured Obsidian vault with the user's selected model and effort. It is a separate visible projectless task in recent tasks; show its link and vault readback without pinning it. Ending status never gates the main result or another task. Skip when no useful memory exists; an unavailable vault or launch capability is pending without local storage.

## Boundaries

Preserve unrelated work. Perform reversible actions within the request; obtain authorization for actions outside it. Never message others without explicit authorization. Only claim model identity or performance backed by evidence.

Apply [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md) to all scripts, tests, and background work, including delegated and nested launches. Capture output without visible windows or focus changes; opening a terminal, browser, report, or app requires an explicit request to show it.

Use [parallel ownership](references/parallel-session-orchestration.md) when delegating and [resource ownership](references/task-resource-lifecycle.md) and the [Cache policy](references/project-cache-artifact-policy.md) when creating temporary resources. These helpers support work; they are not mandatory receipt ceremonies.

---
name: task-analyze-skill
description: "Briefly explain a task's objective and implementation steps before execution, then carry out the work with focused verification."
---

# Task Analyze

Read the request, applicable skills, and relevant existing project memory. Identify the intended result and constraints without importing another project's facts.

Before detailed execution, briefly tell the user what you will achieve and the approximate implementation steps. Use one sentence for simple work and a short ordered plan when steps or dependencies matter. Keep the explanation about the work itself; omit complexity scores, model selection, and execution bookkeeping.

Then follow those steps without waiting for routine confirmation. The user can interrupt or adjust the direction. Ask only when a missing decision materially affects the result or an action requires authorization; continue independent work where possible. Explain a material change in approach before carrying it out.

Verify consequential changes in the active task at the smallest relevant boundary, following [Verify](../verify-skill/SKILL.md). Report the result, evidence, and any remaining limits. Use [Project Memory](../project-memory-skill/SKILL.md) only for relevant recall or useful durable updates; Ending is memory-only.

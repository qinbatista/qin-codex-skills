---
name: task-analyze-skill
description: "Use for model selection, bounded delegation, dependency planning, or routing maintenance. Keep skill-governed work on the user's selected model and effort."
---

# Task Analyze

The user's selected model reads the request, related skills and relevant existing project memory, then defines clear goals, constraints and completion evidence. Ordinary work can stay in this session. Use a plan or child tasks only when they make the work easier or faster.

## Visible task contract

Show `Complexity: score/100 (band) · Model: model|effort · Route: change or no switch` before execution. Scores are estimates: small 0–24, standard 25–49, complex 50–74, advanced 75–100. Explain the relevant routing reason. For delegated work show each goal, score, pair, dependencies and status; update with actual runtime pairs after completion. An assignment, mock process or configured model is not live execution proof. Direct tool work does not need a model call merely to display a score.

## Model boundary

- A task governed by a user's skill keeps the user's selected model **and reasoning effort**. This includes coding style, code structure, UI design, prompts, and memory summarization. An incidental shell command or a smaller complexity score does not remove those constraints.
- An independent task with no governing skill may choose a suitable available model using complexity and proven outcomes from the same project. Examples include collecting command output or applying a clear mechanical transformation when no user's skill governs it.
- Identify actual governing skills before routing. Carry their names and constraints into child goals. Routing/workflow machinery by itself does not make a task skill-governed. Missing selected-model identity means retain the current session; never silently substitute a cheaper model.
- Keep the selected pair after a quality or provider failure on governed work. Diagnose or retry within the task; request a model change only if it is actually needed. Automatic adjustment remains available for independent tasks.

## Execute and verify

Give each delegated task a goal, inputs, output, write boundary, dependencies and stop condition. Parallelize independent branches with disjoint state; keep shared writes and output dependencies ordered. The main task integrates the results and owns completion.

Verify meaningful or complex changes **inside the active task** with the smallest relevant behavior check. For UI changes, inspect the changed rendered behavior when practical. Skip verification for simple value-only edits. Do not start a whole project or compile the whole project unless the user asks. Report what the evidence proves and any remaining limitation.

Ending only summarizes useful changes, architecture decisions and preferences into existing scoped project memory, using the user's selected model and effort. Under the user-authorized Ending lifecycle, it runs as one separate visible projectless task after the final result and its verification. Show its task link and scoped memory readback; a launch packet alone is pending. It does not verify, run builds, repair or launch another task chain. No durable new information or missing memory means an explicit skip.

## Memory and routing tools

Read only related memory for the identified project/module; explicit global preferences apply only when relevant. Missing or unconfigured memory is optional. Never substitute another project's memory or create empty memory structures during routing.

[`selected_model_policy.py`](scripts/selected_model_policy.py) enforces the model boundary in the runner and dispatcher. [`obsidian_adaptive_model_runner.py`](scripts/obsidian_adaptive_model_runner.py) accepts `--governing-skill` and the selected `--entry-model`/`--entry-effort`. `--skill-independent` is a planner classification and cannot override named governing skills. [`task_route_dispatcher.py`](scripts/task_route_dispatcher.py) executes an optional dependency plan and rebinds governed nodes at execution as well as validation.

Read [route contract](references/route-contract.md) for machine fields, [adaptive routing](references/adaptive-routing.md) for independent-task learning, and [related memory](references/related-memory.md) for scope. Keep model claims tied to actual selection or runtime evidence; don't claim savings without comparable token/time measurements.

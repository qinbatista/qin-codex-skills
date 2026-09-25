---
name: task-analyze-skill
description: "Use for model selection, bounded delegation, dependency planning, or routing maintenance. Keep skill-governed work on the user's selected model and effort."
---

# Task Analyze

The user's selected model reads the request, related skills and relevant existing project memory, then defines clear goals, constraints and completion evidence. Ordinary work can stay in this session. Use a plan or child tasks only when they make the work easier or faster.

## Visible task contract

Show `Complexity: score/100 (band) · Model: model|effort · Route: change or no switch` before execution. Scores are estimates: small 0–24, standard 25–49, complex 50–74, advanced 75–100. For delegated work show each goal, score, pair, dependencies and status; update with actual runtime pairs after completion. An assignment or configured model is not live execution proof. Direct tool work needs no extra model call.

## Model boundary

- A task governed by a user's skill keeps the user's selected model **and reasoning effort**. This includes coding style, code structure, UI design, prompts, and memory summarization. An incidental shell command or a smaller complexity score does not remove those constraints.
- The available route models are `gpt-6-luna`, `gpt-6-sol`, and `gpt-6-astra`. Luna suits bounded work, Sol general implementation, and Astra demanding synthesis or high uncertainty. Use only provider-supported efforts: `low` (the user's "light"), `medium`, `high`, `xhigh`, `max`, and `ultra` where available. Luna currently stops at `max`; disclose an unsupported pair instead of silently changing the model or effort.
- An independent task with no governing skill may choose among those three using its purpose, complexity, and verified outcomes from the same project. Repeated steps with a stable contract should become a local script when that reduces future work.
- Identify actual governing skills before routing. Carry their names and constraints into child goals. Routing/workflow machinery by itself does not make a task skill-governed. Missing selected-model identity means retain the current session; never silently substitute a cheaper model.
- Keep the selected pair after a quality or provider failure on governed work. Diagnose or retry within the task; request a model change only if it is actually needed. Automatic adjustment remains available for independent tasks.

## Execute and verify

Give each delegated task a goal, inputs, output, write boundary, dependencies and stop condition. Parallelize independent branches with disjoint state; keep shared writes and output dependencies ordered. The main task integrates the results and owns completion.

Verify changed code and consequential outputs **inside the active task** with a real execution or artifact readback at the relevant boundary. Use one verification path; do not label a quick or mocked check as acceptance. For UI changes, inspect the rendered behavior. Do not start or compile a whole project unless requested. Fix failures in this task and report remaining limits.

Ending only updates useful, scoped memory in the configured Obsidian vault after the main task and its real verification are complete. It is a separate projectless task in Codex's recent tasks, never pinned or used as a gate for the main task or another task. Show its task link and vault readback when run; skip when nothing durable changed. An unavailable vault leaves the memory write pending without Codex-local storage. Ending never tests, repairs, benchmarks, publishes, or launches further tasks.

## Memory and routing tools

Ensure the Obsidian memory vault through [Project Memory](../project-memory-skill/SKILL.md), then read only related memory for the identified project/module; explicit global preferences apply only when relevant. Missing matching records are a normal skip. Never substitute another project's memory or create empty project notes during routing.

[`selected_model_policy.py`](scripts/selected_model_policy.py) enforces the model boundary in the runner and dispatcher. [`obsidian_adaptive_model_runner.py`](scripts/obsidian_adaptive_model_runner.py) accepts `--governing-skill` and the selected `--entry-model`/`--entry-effort`. `--skill-independent` is a planner classification and cannot override named governing skills. [`task_route_dispatcher.py`](scripts/task_route_dispatcher.py) executes an optional dependency plan and rebinds governed nodes at execution as well as validation.

Read [route contract](references/route-contract.md) for machine fields, [adaptive routing](references/adaptive-routing.md) for independent-task learning, and [related memory](references/related-memory.md) for scope. Keep model claims tied to actual selection or runtime evidence; don't claim savings without comparable token/time measurements.

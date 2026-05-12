---
name: qin-easy-code-spark
description: Prefer GPT-5.3-Codex-Spark for obvious, bounded, low-risk coding work when Codex has a model-selection or allowed delegation surface available. Use when the expected implementation, review, cleanup, or verification path is clear from the request or nearby code, even if the task is more than a tiny edit; avoid using it for unclear debugging, architecture, multi-system changes, high-risk migrations, or tasks that require deeper reasoning.
---

# Qin Easy Code Spark

## Overview

Use this skill to route obvious bounded coding work to `GPT-5.3-Codex-Spark` when model switching is available. The trigger is not limited to tiny edits: if the task is clear, low-risk, and has a straightforward verification path, Spark should be used through an available allowed model route. This skill only guides model choice; it does not replace project instructions, coding standards, testing requirements, or task-specific skills.

## Trigger

Use this skill when the user explicitly asks for Spark, `GPT-5.3-Codex-Spark`, or an obvious bounded coding task that is clear enough for Spark to handle through an available model route.

## Quick Decision

Classify the task before implementation.

Use `GPT-5.3-Codex-Spark` when all of these are true:

- The request is clearly bounded and likely affects one or a few files.
- The expected edit, review target, cleanup path, or verification action is already obvious from the request, nearby code, or a shallow inspection.
- The task can be non-trivial, but the correct next action and success criteria are clear.
- The task does not require deep repository archaeology, ambiguous product judgment, architecture changes, or difficult debugging.
- Verification is simple, such as a focused lint, test, build, type check, or direct file inspection.

Keep the current stronger model when any of these are true:

- The task spans multiple subsystems, data contracts, build tools, or deployment behavior.
- The failure is unclear, intermittent, or needs substantial debugging.
- The change is security-sensitive, financial, auth-related, destructive, or migration-heavy.
- The user asks for a deep review, broad refactor, architecture plan, or difficult performance work.
- The task only becomes clear after significant investigation, even if the final edit is small.

## Model Routing

When the active environment lets Codex choose a model for the work, select:

```text
GPT-5.3-Codex-Spark
```

When an API or tool requires the model id, use:

```text
gpt-5.3-codex-spark
```

If the current Codex session cannot switch the active model directly, continue with the current model and do not block the task. Use Spark only through an existing allowed model-selection path, such as an explicit user-approved delegation surface or another environment-provided model picker.

## Workflow

When Spark is the right route, dispatch it like a worker agent instead of treating it as a synchronous helper call:

1. Give Spark the complete task prompt up front, including target files, repo constraints, relevant skills or style rules, success criteria, and exact verification commands when known.
2. Tell Spark it is not alone in the codebase, should preserve unrelated edits, and should report the files it changed plus tests it ran.
3. After dispatch, keep the parent model moving on non-overlapping work when possible instead of waiting by default.
4. Wait for Spark only when its result blocks the next parent action, when integration/review is needed, or before the final response if Spark owns part of the requested deliverable.
5. Review Spark's output before finalizing. Keep useful edits, trim over-broad changes, and run the required verification in the parent context when practical.

## Local Codex CLI Delegation

Use local delegation for obvious, bounded, low-risk coding work when you want to run a separate Codex process rather than switch the current parent chat model.

```bash
codex exec --model gpt-5.3-codex-spark -C /path/to/repo "Apply the requested bounded change. Preserve unrelated edits. Report changed files and tests."
```

(`-m` is the short form of `--model`.)

Use this when the task is suitable for Spark and the local CLI runner is the intended execution path. This runs as a separate local Codex process and does not change the active model for the parent conversation.

Do not dispatch Spark with a vague placeholder and then wait to feed it the real prompt. Put the real task, constraints, and verification expectations into the initial Spark prompt. If the parent session has enough work to continue safely, leave Spark running in the background and poll it later only when needed.

Do not spawn a subagent solely because this skill loaded. Follow the active system and developer rules for when delegation is allowed.

When Spark is suitable and an allowed route exists, trigger that route instead of silently continuing on the parent model. If no allowed route exists in the current environment, continue with the current model and mention the limitation when it matters.

## Guardrails

- Spark delegation does not relax repo instructions, skill requirements, verification rules, or user constraints.
- Do not use Spark for unclear debugging, architecture, broad migrations, security-sensitive changes, or work that needs deep reasoning.
- Do not let a background Spark run own the final answer unchecked; review, integrate, and verify the relevant result before claiming the user request is complete.
- Do not block the parent model waiting for Spark when there is safe non-overlapping work to do.

## Interaction With Other Skills

Load any task-specific or repo-required coding skills as usual. This skill only decides whether the easy edit can run on Spark; other skills still control implementation style, project rules, and verification.

If another instruction explicitly requires a stronger model, a different named model, or no model switch, obey the more specific instruction.

## Examples

Good Spark candidates:

- Rename a button label in one component.
- Fix a misspelled variable introduced by the current change.
- Add a missing import for an obvious compile error.
- Adjust a CSS spacing value or a simple responsive rule.
- Update a small test expectation after an intentional behavior change.
- Apply an obvious single-agent prompt or skill wording correction.
- Review a named file for clear local optimization opportunities when the scope and success criteria are bounded.
- Run a focused verification pass where the command and expected evidence are clear.

Keep a stronger model:

- Investigate a flaky production bug.
- Redesign a shared API contract.
- Migrate a framework or dependency across many files.
- Review an unfamiliar security-sensitive auth flow.

---
name: optimization-skill
description: "Plan local execution for repeatable work and make authorized optimizations. Reuse existing commands, preserve intended behavior, and measure claimed gains."
---

# Optimization Skill

Before writing benchmarks, fixtures, reports or other task support, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Resolve the isolated project Cache owner before the first write, including tool caches.

## Scope

Optimize only the requested code, prompt, Skill, or process. Briefly explain the intended improvement and implementation steps before detailed execution.

Read relevant project memory on every task through [project memory](../project-memory-skill/SKILL.md). If unavailable, continue. Keep projects separate and use fresh evidence over stale notes. Record shared preferences globally only when the user makes them global.

## Run repeatable work locally

Choose test, diagnostic, or other multi-step operations that can run consistently from explicit inputs and produce a checkable result. Reuse an existing test runner, CLI, or script that performs the work in one local command. If no command fits, implement a small parameterized helper with the project or Skill that owns the operation when the task authorizes it and expected reuse justifies maintaining it. Keep one-run adapters in task Cache.

Document the reusable command, its inputs, expected output, and how it signals failure. Run it in the active task with a representative input and verify the output and any failure behavior that affects acceptance. Use the result to guide diagnosis and decisions that require judgment.

## Workflow

1. Identify the owning path, expected output, and behavior that must remain: order, side effects, cancellation, failure semantics, and public contracts.
2. Capture a representative baseline when claiming performance or behavior preservation.
3. Choose the smallest useful change. Use [local execution](#run-repeatable-work-locally) for suitable repeatable steps. Apply [Management's authoring rules](../management-skill/SKILL.md#authoring-rules) to Skill revisions.
4. Apply the relevant code or prompt preferences and change only the authorized scope.
5. Verify during the active task with identical inputs and the smallest real comparison or output readback. For complex or high-risk changes, an independent review can run inside the same task. Do not start or compile the whole project unless requested.
6. Report the verified result, any measured gains, and remaining limitations. Ending records useful project memory alongside [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md); it does not re-verify, repair code or benchmark.

For a Skill review, the optional `scripts/skill_optimizer.py` supports `scan <skills-root>` to list Skills and `audit <skill-path>` to check references, duplicate instructions, and possible uses for local tools. Run `verify <skill-path>` to check references and supported scripts in one command.

For `verify`, Python syntax is checked in memory. macOS AppleScript compilation requires `TMPDIR`, `TEMP` or `TMP` to point inside the current project's `Cache/temp-*` run; without that owner, the check reports an error instead of writing to system temporary storage.

## Verification and measurement

Check output equivalence or the intentional behavior difference, including ordering, side effects, error handling, and cancellation. Parallel changes also preserve deterministic collection and isolate writes; compare critical-path elapsed time, not summed worker durations.

Claims require measured evidence:

- Use comparable inputs, scope, configuration, and acceptance criteria.
- Report end-to-end elapsed time and relevant resource use, including material retry overhead; component timings may explain the result but cannot substitute for totals.
- Keep cached input and reasoning output separate without double-counting them.
- A single run is a smoke result. Use repeated, preferably alternating trials for a stable speed/cost claim.
- A failed output invalidates its savings claim. Text size reduction alone is not measured token or runtime savings.

If independent verification was not performed, do not call the work independently verified. If the meaningful comparison cannot run, state that limit rather than inventing proof or starting unrelated infrastructure.

## Guardrails

Preserve behavior unless the user changes the goal. Do not broaden another task to implement an optimization discovered along the way. Keep support artifacts under the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md), and publish only when authorized.

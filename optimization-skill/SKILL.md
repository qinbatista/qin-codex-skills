---
name: optimization-skill
description: "Use for requested optimization or an authorized reusable workflow improvement. Preserve intended behavior and measure claimed gains; repetition or shorter prose alone is not a reason to expand scope."
---

# Optimization Skill

## Scope

Optimize only the requested code, prompt, Skill, or process. The user's selected model and effort handle work governed by relevant Skills; the main model defines the goals. Skill-free mechanical measurements or execution may use adaptive routing.

Read relevant project memory on every task through [project memory](../project-memory-skill/SKILL.md). If unavailable, continue. Keep projects separate and use fresh evidence over stale notes. Record shared preferences globally only when the user makes them global.

## Workflow

1. Identify the owning path, expected output, and behavior that must remain: order, side effects, cancellation, failure semantics, and public contracts.
2. Capture a representative baseline when claiming performance or behavior preservation.
3. Choose the smallest useful change. Keep judgment in the Skill, long optional context in references, repeatable mechanics in scripts, and reusable fixtures in assets. Do not replace sound reasoning with brittle automation.
4. Apply the relevant code or prompt preferences and change only the authorized scope.
5. Verify during the active task with identical inputs and the smallest convincing comparison. For complex or high-risk changes, an independent review can run inside the same task. Simple value-only edits may skip verification. Do not start or compile the whole project unless requested.
6. Report the artifact, measured comparison, and remaining limitations. Ending only writes concise project memory with the user's selected model and effort; it does not verify, repair, or benchmark.

For a Skill-root review, the optional `scripts/skill_optimizer.py scan <skills-root>` lists visible Skills; `audit <skill-path>` checks references and duplicate instructions. Use these when they save work, not as required pre-reading ceremony.

## Verification and measurement

Check output equivalence or the intentional behavior difference, including ordering, side effects, error handling, and cancellation. Parallel changes also preserve deterministic collection and isolate writes; compare critical-path elapsed time, not summed worker durations.

Claims require measured evidence:

- Use comparable inputs, scope, configuration, and acceptance criteria.
- Report end-to-end elapsed time and total tokens, including material routing/retry overhead; component timings may explain the result but cannot substitute for totals.
- Keep cached input and reasoning output separate without double-counting them.
- A single run is a smoke result. Use repeated, preferably alternating trials for a stable speed/cost claim.
- A failed output invalidates its savings claim. Text size reduction alone is not measured token or runtime savings.

If independent verification was not performed, do not call the work independently verified. If the meaningful comparison cannot run, state that limit rather than inventing proof or starting unrelated infrastructure.

## Guardrails

Preserve behavior unless the user changes the goal. Do not broaden another task to implement an optimization discovered along the way. Keep support artifacts under the [project Cache policy](../workflow-skill/references/project-cache-artifact-policy.md), and publish only when authorized.

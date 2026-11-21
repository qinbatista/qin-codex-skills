---
name: optimization-skill
description: "Plan local execution for repeatable work and make authorized optimizations. Reuse existing commands, preserve intended behavior, and measure claimed gains."
---

# Optimization Skill

Keep benchmarks, fixtures, reports and tool caches in their isolated owner from the first write under the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md).

## Scope

Optimize only the requested code, prompt, Skill or process. Briefly state the intended improvement and steps before detailed execution. Recall scoped [project memory](../project-memory-skill/SKILL.md) when available and prefer current evidence. Store preferences globally only when the user makes them global.

## Run repeatable work locally

For repeatable tests, diagnostics or other multi-step work with explicit inputs and checkable results, prefer one local command using an existing runner, CLI or script. Add a small parameterized helper in the owning project or Skill only when authorized and justified by reuse. Keep one-run adapters in task Cache.

Document the command, inputs, output and failure signal. Run it here with a representative input to verify the output and any failure behavior material to acceptance. Use the evidence to guide diagnosis.

## Workflow

1. Identify the owner, output and behavior to preserve, including order, side effects, cancellation, failures and public contracts. Capture a representative baseline for performance or preservation claims.
2. Make the smallest useful authorized change. Apply applicable code or prompt rules, [local execution](#run-repeatable-work-locally) and [Management's authoring rules](../management-skill/SKILL.md#authoring-rules) for Skill revisions.
3. Verify here with identical inputs and the smallest real comparison or readback. Use independent review when useful for complex or high-risk changes. Whole-project startup or builds require a request.
4. Report verified results, measured gains and limits. Use [Project Memory's inline closeout](../project-memory-skill/SKILL.md#inline-guidance-memory-and-resource-closure) and [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md) for memory and resources. Finish testing, repair and measurement in the active task.

For Skill reviews, `scripts/skill_optimizer.py` optionally lists Skills with `scan <skills-root>`, flags reference or repetition issues and local tool candidates with `audit <skill-path>`, and checks references and scripts with `verify <skill-path>`. Python syntax checks run in memory. macOS AppleScript compilation fails unless `TMPDIR`, `TEMP` or `TMP` points inside the current project's `Cache/temp-*` run.

## Verification and measurement

Compare outputs and the relevant behavior, including order, side effects, errors and cancellation. For parallel changes, preserve deterministic collection and isolated writes, and measure elapsed time on the critical path.

- Use comparable inputs, scope, configuration, and acceptance criteria.
- Report end-to-end time and resource use, including retry overhead. Use component timings to explain those totals.
- Count cached input and reasoning output separately without double-counting.
- Support stable speed or cost claims with repeated, preferably alternating trials that pass acceptance. Report text size as text size. Token and runtime savings require measurement.
- State any missing comparison or independent verification. Avoid starting unrelated infrastructure to fill an evidence gap.

## Guardrails

Preserve behavior unless the user changes the goal. Leave incidental optimization ideas outside the current task's scope. Publish only when authorized.

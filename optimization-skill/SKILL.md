---
name: optimization-skill
description: "Optimization executor selected by the locked task-analyze-skill plan. Use for explicit optimization or stable repeated workflows that can safely become simpler instructions, references, scripts, assets, templates, or dependency-safe parallel work. Basic implementation may reach the main result after Mini Verify; same-behavior, token/time, and regression proof belongs to a different verifier in background Ending Task."
---

# Optimization Skill

Use this skill only when the locked `task-analyze-skill` plan includes an optimization node. It may implement an explicitly requested optimization or a post-result Ending Task improvement, but it never verifies its own behavior.

## Trigger

Use when:

- the user explicitly asks to optimize a skill, prompt, process, model workflow, code path, or repeated Codex behavior;
- substantially the same workflow has repeated at least three times;
- deterministic mechanics can safely move into a script/reference/template/asset;
- dependency analysis proves independent work can become parallel without changing behavior.

Do not optimize merely because code or prose could be shorter. Preserve the owning skill, observable behavior, order, side effects, error semantics, and authorized scope.

## Internal Route Selection

Select only the optimization form returned by Task Analyze: tighter rule, reference, script, asset, template, or dependency-safe parallel topology. Combine forms only when the locked plan requires them.

## Main Result And Ending Task Placement

- If optimization is the user's requested artifact, implement the smallest safe change on the result path, run Mini Verify, and show the basic result.
- If optimization is discovered while doing another task, do not expand the main scope; return it as a candidate for planned Ending Task.
- Same-behavior Real Verify, token/time comparison, broad regression, and independent optimization verification always run after the main result in Ending Task.
- Do not call the optimization independently verified until the different verifier passes. If it fails, notify the user and reopen the task.

## Model Contract

Follow the exact model and effort in the locked plan:

- Terra normally owns grounded optimization design, dependency analysis, before/after review, and independent comparison.
- Spark first owns Python/C#/Unity C# helper or implementation nodes through `code-skill`.
- Luna owns direct bounded instruction/reference/template updates and lightweight records.
- Sol owns unresolved architecture or genuinely difficult cross-system optimization judgment.

The entry model is not inherited. A label is not execution proof; use runtime receipts when model routing or savings is part of acceptance.

## Workflow

1. Identify the owning skill/process and observable behavior to preserve.
2. Capture raw before input, method, output, tokens/time when relevant, order, side effects, and failure behavior.
3. Select the smallest reusable form: tighter rule, reference, script, asset, template, or safe parallel topology.
4. Use `code-skill` for every Python/C# implementation or authored probe.
5. Implement only the authorized optimization.
6. Return raw after artifacts plus a focused Mini Verify target.
7. After Mini Verify, allow the main result to be shown.
8. Hand optimizer identity, files, commands, before/after evidence, and remaining risks to a different Ending Task verifier.

## Independent Verification Contract

The optimization implementer and verifier must be different workers/agents. The Ending verifier uses `verify-skill` and reports:

- optimizer and verifier identities;
- identical before/after inputs and acceptance criteria;
- output equivalence or intentional documented differences;
- dependency, order, side-effect, and error-semantic preservation;
- routed versus baseline tokens and elapsed time when savings are claimed;
- failures, repairs needed, and whether the task must reopen.

If no different verifier is callable, report `independent optimization verification blocked`. Do not substitute implementer self-review.

## Token And Time Claims

Do not claim savings from shorter text, different prompts, different inputs, or summed parallel branch times.

- Compare identical task scope, prompts, inputs, topology, sandbox, and acceptance criteria.
- Keep cached input separate; it is already part of input tokens.
- Keep reasoning output separate; it is already part of output tokens.
- Compare critical-path elapsed time for parallel workflows.
- Treat one pair as a smoke result; prefer alternating repeated runs and medians.

## Generated File Placement

### Reusable Resources

- Keep judgment and trigger logic in `SKILL.md`.
- Move stable long context into `references/`.
- Move deterministic repeatable mechanics into `scripts/`.
- Put reusable fixtures/templates/media in `assets/`.
- Put temporary evidence in `cache/` or the active task `work/` area.
- Do not create new global skills unless the user explicitly authorizes that global skill change.

## Guardrails

- Do not optimize before the requested base behavior exists.
- Do not move reasoning-heavy judgment into brittle code.
- Do not parallelize shared-state, ordered, Unity main-thread, or side-effect-heavy work without proof.
- Do not push/publish unless explicitly authorized.
- Do not wait to show the Mini-verified basic result for broader Ending Task comparison.

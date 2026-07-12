---
name: optimization-skill
description: "Do not infer optimization from repeated benchmark arms or exact-scoped read-only work. Use only for user-requested optimization, an explicitly authorized reusable workflow improvement, or a positively admitted optimization node. Independent proof still requires a different verifier after the result."
---

# Optimization Skill

Do not infer optimization from repeated benchmark arms or exact-scoped read-only work. Use this skill directly only when the user requests optimization or explicitly authorizes a reusable workflow improvement, or execute it as an exact node when Task Analyze has positively admitted a delegated route. Inline optimization uses the current model and no foreground verifier, Workflow, or child receipt. An admitted node preserves its locked pair and dependencies. In both modes, the optimizer never verifies its own behavior.

## Trigger

Use when:

- the user explicitly asks to optimize a skill, prompt, process, model workflow, code path, or repeated Codex behavior;
- substantially the same workflow has repeated at least three times;
- deterministic mechanics can safely move into a script/reference/template/asset;
- dependency analysis proves independent work can become parallel without changing behavior.

Do not optimize merely because code or prose could be shorter. Preserve the owning skill, observable behavior, order, side effects, error semantics, and authorized scope.

## Internal Route Selection

Select only the optimization form required by the inline request or admitted node: tighter rule, reference, script, asset, template, or dependency-safe parallel topology. Combine forms only when the requested outcome or locked node requires them.

## Main Result And Ending Task Placement

- If optimization is the user's requested artifact, implement the smallest safe change and show the completed result immediately; independent Real Verify follows in Ending Task.
- If optimization is discovered while doing another task, do not expand the main scope; report it as a candidate. Only an admitted route may place authorized follow-up work in Ending Task.
- Same-behavior Real Verify, token/time comparison, broad regression, and independent optimization verification run after the main result when genuinely required. Inline execution may call a different verifier directly; an admitted route uses Ending Task.
- Do not call the optimization independently verified until the different verifier passes. If it fails, notify the user and reopen the task.

## Model Contract

Ordinary inline optimization intentionally uses the current user-selected model and performs no foreground downgrade/upgrade trial. An admitted optimization node follows the exact model and effort in the locked plan:

- Luna, Terra, and Sol roles are cold-start hints only; the exact similar-task profile learns across the effort-first Luna-low through Sol-ultra ladder.
- Every Python/C#/Unity C# helper or implementation node still loads `code-skill`. Explicit benchmark/admitted tiny routes are exactly Spark-low plus the full normal fallback; admitted non-tiny routes retain the exact full normal ladder without Spark, while ordinary inline implementation uses the current model.
- Correctness and quality are eligibility gates. Rank tokens, then process time, then weaker rung only when every compared Real-passing pair shares the same exact workload hash with complete metrics; otherwise use the quality boundary.
- A frozen exact-profile pair is reused until verified failure or material ladder, hard-floor, profile, or policy drift.

An admitted node does not silently inherit or reselect another pair. Inline work intentionally remains on the current model and does not fabricate a receipt. A label is not execution proof; use runtime receipts only when admitted model routing, an explicit benchmark, or savings is part of acceptance.

## Workflow

1. Identify the owning skill/process and observable behavior to preserve.
2. Capture raw before input, method, output, tokens/time when relevant, order, side effects, and failure behavior.
3. Select the smallest reusable form: tighter rule, reference, script, asset, template, or safe parallel topology.
4. Use `code-skill` for every Python/C# implementation or authored probe.
5. Implement only the authorized optimization.
6. Show the raw after artifact immediately; do not add a foreground verifier or child receipt.
7. After presentation, hand the before/after evidence to an independent Ending Real verifier without changing the locked route.
8. When independent proof is required, hand optimizer identity, files, commands, before/after evidence, and remaining risks to a different verifier after the main result.

## Independent Verification Contract

The optimization implementer and verifier must be different workers/agents. An inline task may call a different `verify-skill` worker after the main result; an admitted task uses its Ending verifier. The verifier reports:

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
- To compare Direct versus Global, keep user/project configuration identical. Run Direct with the exact raw prompt through `model_execution_receipt.py run --direct-task --benchmark-run-id benchmark-...` and Global through `--bootstrap-task --benchmark-run-id benchmark-...`; neither arm enters Task Analyze context or adds `LOCKED_ROUTE_NODE`, and neither uses `--ignore-user-config`.
- Aggregate every unique entry, collaboration, dispatcher, retry, and incomplete worker session exactly once. Never count a canonical receipt and its matching attempt receipt twice.
- Treat first-result foreground tokens/time as the user task cost. Record Ending Real totals only as diagnostics; exclude all Ending/verification time and tokens from task-cost and admission comparisons. A timeout or missing final result fails the optimization gate and cannot support a savings claim.
- Keep cached input separate; it is already part of input tokens.
- Keep reasoning output separate; it is already part of output tokens.
- Compare critical-path elapsed time for parallel workflows.
- Treat one pair as a smoke result; prefer alternating repeated runs and medians.
- Never let faster execution override a higher total-token result when the routing objective is token-first, time-second.

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
- Do not wait to show the completed result for Ending Task comparison.

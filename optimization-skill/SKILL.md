---
name: optimization-skill
description: "Do not infer optimization from repeated benchmark arms or exact-scoped read-only work. Use only for user-requested optimization, an explicitly authorized reusable workflow improvement, or a positively admitted optimization node. Independent proof still requires a different verifier after the result."
---

# Optimization Skill

Do not infer optimization from repeated benchmark arms or exact-scoped read-only work. Use this skill directly only when the user requests optimization or explicitly authorizes a reusable workflow improvement, or execute it as an exact node when Task Analyze has positively admitted a delegated route. Eligible text/code optimization uses the catalog-derived adaptive producer; ineligible tool-only work stays inline. An admitted node preserves its locked pair and dependencies. In every mode, the optimizer never verifies its own behavior.

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
- A non-trivial code or process optimization is material: it emits `ending-required` and requires durable project-memory closeout even when no other surface is declared. Only explicit `trivial_value_only` work with no `real_test`, `information_update`, or `memory_update` surface records `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_or_material_update`. Finish code, run exactly one smallest local Quick Check, present `CODE READY`, then let the parent launch the global projectless Ending and return without polling. Its exact `create_thread` target is `{"type":"projectless"}`; `codex_app__list_threads` must read back `projectId=null` or absent, while project/current-task/same-task-subtask placement is BLOCKED. Spark-xhigh is first; a persisted real quota, five-hour, provider-rate, or trusted retry-after restriction skips the cooling model for the next stronger supported controller until expiry. Same-behavior Real Verify, token/time comparison, broad regression, and independent optimization verification run there when applicable. Saved Terra/Sol `ENDING_CHECK_WORKER` nodes never edit, repair, route, or own lifecycle.
- Do not call the optimization independently verified until the different verifier passes. If it fails, notify the user and reopen the task.

## Model Contract

Eligible optimization production follows the catalog-generated shared ladder and matching Obsidian context. An admitted optimization node follows the exact model and effort in the locked plan:

- Shared role models are cold-start hints only; auto-build or refresh the highest registered numeric GPT family from weakest to strongest and exclude older families from active switching.
- Every Python/C#/Unity C# helper or implementation node still loads `code-skill`. Eligible small low-risk edits run the same-session outcome gate, then try Spark only with no stronger session route; other production executes the saved contextual quality pair. Two Real PASS results permit one-rung descent and verified correctness/quality failure moves one rung up. Spark failure suppresses the matching score band and upgrades the next task. Spark remains available for admitted disjoint source branches.
- Correctness and quality are eligibility gates. Routing always keeps the lowest Real-passing rung above the strongest failed rung; like-for-like token/time evidence evaluates the strategy but never promotes a stronger passing pair over that lowest-correct boundary.
- A frozen exact-profile pair is reused until verified failure or material ladder, hard-floor, profile, or policy drift.

An admitted node does not silently inherit or reselect another pair. Ineligible inline work does not fabricate a receipt. A label is not execution proof; eligible production and any claimed model routing, benchmark, or savings require the matched runtime receipt.

## Workflow

For a whole Skill-root review, use the deterministic helper before prose inspection. `scan` lists only direct visible Skill children and is concise by default; add `--verbose` only when descriptions and headings are needed. Run `audit` once per listed Skill, then `verify` only for changed Skills.

```text
macOS/Linux: python3 optimization-skill/scripts/skill_optimizer.py scan <skills-root>
Windows PowerShell: py -3 optimization-skill\scripts\skill_optimizer.py scan <skills-root>
```

1. Identify the owning skill/process and observable behavior to preserve.
2. Capture raw before input, method, output, tokens/time when relevant, order, side effects, and failure behavior.
3. Select the smallest reusable form: tighter rule, reference, script, asset, template, or safe parallel topology.
4. Use `code-skill` for every Python/C# implementation or authored probe.
5. Implement only the authorized optimization.
6. Show the raw after artifact immediately; do not add a foreground verifier.
7. After presentation, start Ending with the producer receipt when one exists, resolve the exact saved project, and hand the before/after evidence to an independent projectless Ending Real verifier without changing the locked route. Every terminal task remains visible and reports attempts, first/retry pass, suitability, next route, and Obsidian record link/status; never auto-archive or delete it. A failed check creates a fresh independent projectless Repair Task that never contacts, steers, interrupts, terminates, hands off, moves, or mutates an existing session. If an active task owns the write surface, Repair waits without messaging, then performs the scoped repair and starts a fresh parent-linked Ending.
8. Hand optimizer identity, files, commands, before/after evidence, and remaining risks to a different verifier after the main result; trivial non-executable results still use the smallest completion/record check.

## Result Model Disclosure

Use the compact Result Model Disclosure from `task-analyze-skill/references/route-contract.md` verbatim. Do not expand it into the former repeated model, evidence, previous-model, switch-summary, or reason lines.

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
- For adaptive model-matching claims, make the primary comparison the clean stable selected execution after the correct route is known: Direct counts its complete fixed task census and Auto counts its selected child/graph receipt. Exclude matching/controller time, calibration failures, retries, fallbacks, repairs, entry-invariance probes, and Ending from primary token/time savings, but report each separately rather than hiding it.
- Keep actual first-result wait as an end-to-end diagnostic. Never advertise first-result savings unless that metric itself is lower. A timeout, missing final result, unstable/trial route, entry mismatch, or incorrect Ending fails the optimization gate.
- Keep cached input separate; it is already part of input tokens.
- Keep reasoning output separate; it is already part of output tokens.
- Compare critical-path elapsed time for parallel workflows.
- Treat one pair as a smoke result; prefer alternating repeated runs and medians.
- Require every compared result and Ending to be correct, Luna/Sol entry to converge on the same stable route, and both aggregate steady logical tokens and steady execution time to be lower. Keep per-tier regressions visible even when the aggregate verdict passes.

## Generated File Placement

### Reusable Resources

- Keep judgment and trigger logic in `SKILL.md`.
- Move stable long context into `references/`.
- Move deterministic repeatable mechanics into `scripts/`.
- Put reusable fixtures/templates/media in `assets/`.
- Do not create new global skills unless the user explicitly authorizes that global skill change.

### Project Cache Artifact Policy

Before the first Codex-selected project-support write, read and apply [Project Cache Artifact Policy](../workflow-skill/references/project-cache-artifact-policy.md). It is the single authority for Cache categories, portable paths, the AI-only external-path registry, compact `AGENTS.md` guidance, retention, and cleanup handoff. Load it only when this task will create a support artifact; durable requested deliverables remain in their declared source or output paths.

## Guardrails

- Do not optimize before the requested base behavior exists.
- Do not move reasoning-heavy judgment into brittle code.
- Do not parallelize shared-state, ordered, Unity main-thread, or side-effect-heavy work without proof.
- Do not push/publish unless explicitly authorized.
- Do not wait to show the completed result for Ending Task comparison.

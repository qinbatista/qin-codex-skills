---
name: verify-skill
description: "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify. Never add Mini/Fast Verify before the user's first presentation."
---

# Verify Skill

Verification has one category: **Real Verify**. Every user task launches an independent post-result Ending lifecycle, regardless of task level. When another task produces the requested artifact, finish and present that artifact first. The presentation must be a usable result, not a progress sentence: start it with `MAIN RESULT READY`, include the outcome or artifact links, and state `Acceptance: PENDING — Ending Real is starting`. Only afterward may Ending Task load this skill. Do not insert Mini/Fast Verify, a verification model, a reread, or a repair round before first presentation. Follow `references/ending-lifecycle.md`.

An independent same-task subagent is not a detached backend. It still keeps the Codex task active and must never be described as background or non-blocking. True non-blocking verification requires a persistent background Codex task/thread supported by the host and explicit user or active-project authorization for background execution. If that authority or capability is absent, use the same-task mode, say that the task stays open until `PASS` or `BLOCKED`, and do not claim backend execution.

When the user explicitly asks for a test, audit, review, replay, or verification as the primary task, that work is the requested result and runs normally on the current model. It does not need a fabricated pre-result verification phase.

## Result-First Boundary

The required order is:

1. producer completes the requested result;
2. show the result immediately;
3. write a lifecycle start receipt and launch exactly one Ending worker in the authorized execution mode;
4. run one proportional Real Verify while isolated logs/docs may run in parallel;
5. if Real fails, persist the error and failed durable project state before repair;
6. launch repair as a new child lifecycle, present the correction, and use a different Ending verifier;
7. record sanitized routing/memory learning only after that producer's Real verdict.

First-result latency ends at step 2. Ending time is recorded separately and never added to first-result time. In same-task mode the UI may still show the task as active; the `MAIN RESULT READY` block is therefore mandatory so the user can distinguish producer completion from acceptance. In persistent-background mode, the foreground task returns after linking the background task and stating `Acceptance: PENDING`; the background task owns the eventual `PASS` or `BLOCKED` result. A tool's own returned state or process exit is completion evidence for the requested action, not a separate foreground verification pass.

## Execution Modes

### Same-task Ending

- Use one independent `ENDING_TASK_WORKER` subagent.
- State `Ending mode: SAME TASK — this task remains open` immediately after the first result.
- The parent may receive the verdict and perform required ordered bookkeeping, but it must not run its own duplicate tests, launch speculative review agents, or enter narrated fixed-interval polling loops.
- A failed verifier may trigger only the bounded repair lifecycle defined below. It is not permission for open-ended exploration.
- Final still requires `PASS` or `BLOCKED`.

### Persistent-background Ending

- Use only when the user or active project instructions explicitly request background/non-blocking execution and the host exposes a persistent background task/thread mechanism.
- Create one background Codex task after `MAIN RESULT READY`; pass it the lifecycle ID, exact acceptance target, artifact paths, project root, allowed mutation boundary, and origin task ID when available.
- State `Ending mode: BACKGROUND`, link or identify that task, then return the foreground task immediately with `Acceptance: PENDING`.
- The background task—not the returned foreground task—records and reports `PASS` or `BLOCKED`, performs ordered failure logging, and starts any authorized repair lifecycle. It must surface its terminal result to the user in its own task or back to the origin when the host supports that.
- If persistent task creation fails, disclose the fallback and use same-task Ending. Never silently substitute a same-task subagent while still calling it background.

### Required Status Vocabulary

- `MAIN RESULT READY`: producer work is complete and usable, but Ending has not accepted it yet.
- `PASS`: Ending accepted the presented result.
- `REPAIRING`: Ending rejected the presented result and a bounded repair lifecycle is active.
- `BLOCKED`: acceptance could not be established or the repair limit was exhausted.

Do not use `done`, `finished`, `green`, or equivalent unqualified wording while acceptance is pending.

Final requires lifecycle PASS or explicit BLOCKED. No hook is used or installed.

## Real Verify Scope

Choose the smallest realistic evidence that tests the observable result:

- exact source/output comparison, schema, parse, syntax, compile, import, or focused execution;
- realistic edited-path behavior, regression, error semantics, side effects, and ordering;
- UI render, responsive layout, interactions, console state, and screenshots;
- image, PDF, document, report, table, typography, clipping, and source-backed correctness;
- browser, desktop app, deployment, automation, or live-environment state;
- prompt behavior across representative cases;
- model-route receipts, session census, token totals, and first-result timing;
- same-behavior optimization comparison with independent verification.

Do not expand a bounded task into an exhaustive suite. Do not relabel a shallow check as production proof. If a repository rule requires broader regression or visual evidence, perform it in Ending Real and report its cost separately.

## Grounded And Routed Results

For receipt-backed grounded JSON, Ending Real may use `../task-analyze-skill/scripts/grounded_result_gate.py` with required keys/order, sorted-array pointers, and an optional source pointer/root. The producer result must already have been presented. The gate validates binding and evidence; it never delays first presentation.

An admitted verification node preserves the locked model, effort, dependencies, input, output, and stop condition. Runtime labels are not proof; use the sanitized receipt contract in `../task-analyze-skill/references/runtime-receipts.md`. Ordinary inline Real Verify uses the current user-selected model and needs no fabricated child receipt.

Routing quality learning records only the producer pair after Real. For a matched adaptive producer receipt, use `../project-memory-skill/scripts/obsidian_model_memory.py record` with the same project/task/module/file/symbol/code context. Obsidian `Projects/<project-key>/ModelExperience` is the sole active private authority; old local `model_experience.json` and central `TaskModelExperience/` are legacy read-only only. Spark is an active priority text/code producer at low/high effort, and its matched Real verdict may be recorded. Operational failures are neutral; a Spark correctness/quality failure starts a new 5.6 repair lifecycle. A verifier pair is never recorded as the producer pair, and inline work without a producer receipt never fabricates learning.

## Real Verify Workflow

1. Read the observable acceptance target and the already-presented result.
2. Select one realistic evidence path proportional to risk.
3. Run or inspect the actual artifact/state.
4. Record input, method, observed output, and pass/fail reason.
5. On pass, record lifecycle `PASS`, finish Ending Task, and update only related sanitized learning.
6. On correctness failure, record lifecycle `FAIL` before repair and notify with `REPAIRING`; never let a background failure disappear.
7. A repair uses a new lifecycle ID and cannot self-verify; its corrected result receives a new independent Ending pass.

## Artifact Guidance

### Code And Scripts

Use syntax/compile/import plus a focused real input/output when proportional. For shared or risky logic, add realistic regressions, error paths, side effects, ordering, or live Unity/runtime evidence. Active code-domain probe authoring uses `code-skill`.

### Skills And Instructions

Check frontmatter, loader limits, referenced files, positive/negative contract scenarios, live task replay, runtime model/effort receipt, stale-name cleanup, and mirror behavior as applicable. Static wording alone does not prove routing behavior.

### UI And Visual Artifacts

Open/render the real artifact; inspect desktop and narrow states, interactions, layout, hierarchy, clipping, readability, consistency, and applicable taste rules. Use `references/visual-verification-rubric.md` and `references/ui-problem-index.md` when relevant.

### Documents And Reports

Parse and render the actual file; inspect page count, required sections, typography, spacing, clipping, tables, hierarchy, and source-backed correctness. Use `references/report-manifest.md` for formal reports.

### Browser, Computer, Automation, And Deployment

Execute the real interaction path, inspect errors and side effects, and confirm final observable state. Production/public actions still require authority before execution; authority is a safety precondition, not verification.

## Obsidian And Optimization

For connected projects or repeated failures, Ending Real may read only directly related Obsidian pages and prior failure lessons. Missing memory is a successful no-op: no local model-learning substitute is created, and future selection remains shared cold-start/inline. Save sanitized lessons only; never store secrets or raw private transcripts.

Optimization verification is independent Ending Real. Require different optimizer/verifier identities, raw before/after inputs and outputs, same-behavior acceptance, token and first-result measurements when claimed, and dependency/order/side-effect/error checks. If no independent verifier is callable, report it as blocked; do not self-certify.

## Evidence Output

Report:

- `Category`: Real Verify;
- `Input`;
- `Used`;
- `Output`;
- `Why pass/fail`;
- `First-result time` and separate `Ending time`, when performance matters;
- `Model receipt`, when routing is part of acceptance.

Create a formal report only when requested or when evidence is long, visual, comparison-heavy, or repository-required. Put temporary evidence under task/project `cache/` or `work/`; final reports go only to the requested output location.

## Guardrails

- Never gate first presentation with Mini/Fast Verify.
- Never call a same-task subagent a backend/background worker.
- Never substitute a progress update such as `implementation complete` for the required usable `MAIN RESULT READY` presentation.
- Never launch multiple overlapping verifier/review workers for one lifecycle; one Ending worker owns the verdict.
- Never hide task state behind repeated `wait` updates. Report only a changed status: `MAIN RESULT READY`, `REPAIRING`, `PASS`, or `BLOCKED`.
- Verify the user's observable result, not only the attempted method.
- Do not hide uncertainty or a blocked environment.
- Do not claim a model ran without runtime evidence.
- Do not let Ending Real alter the already-presented result silently; any repair is a new result lifecycle that is explicitly re-presented.
- Notify and reopen on correctness failure.
- Do not let an optimization implementer verify its own work.
- Do not push, deploy, or send external messages without authorization.

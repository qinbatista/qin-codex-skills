---
name: verify-skill
description: "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify in a separate persistent thread. A producer-side bounded Quick Check may precede code presentation; it is not independent verification."
---

# Verify Skill

Verification has two scopes: user-requested verification as the task itself, and a <=60-second post-result Ending handoff audit. Every non-Ending user task creates that separate persistent Codex thread, but its audit is evidence-only: it does not run extra tests, APIs, broad regression, user questions, waits, or automatic repair. Code producers first apply the bounded Quick Check defined by `code-skill`; that check is completion evidence. After Quick Check, present the usable result as `CODE READY` or `MAIN RESULT READY`, include PASS/SKIPPED evidence, start the lifecycle ledger, create a persistent thread, and rename it exactly `End Task-{concise related task name}`. Link it and return without waiting. A concurrent state change records terminal BLOCKED and exits; it never gates the delivered result. Follow `references/ending-lifecycle.md`.

Never add Mini/Fast Verify before the user's first presentation. The Ending audit has no extra tests, APIs, broad regression, user questions, waits, or automatic repair.

A same-task subagent is forbidden for Ending because it keeps the origin task active. Use the host's persistent `create_thread` capability, then `set_thread_title` for the exact title. The global lifecycle authorizes this background task. If persistent task creation is unavailable or fails, disclose that the audit was unavailable but keep the already-delivered result complete; do not silently substitute a subagent or wait loop.

When the user explicitly asks for a test, audit, review, replay, or verification as the primary task, that work is the requested result and runs normally on the current model. It does not need a fabricated pre-result verification phase.

## Result-First Boundary

The required order is:

1. producer completes the requested result and, for code, runs one bounded Quick Check;
2. show the result immediately with Quick Check PASS/SKIPPED evidence;
3. write a lifecycle start receipt, add `--producer-receipt` when an adaptive producer created the result, create a separate persistent Codex thread, rename it `End Task-{concise related task name}`, and pass the exact handoff;
4. run one bounded read-only handoff audit and end within 60 seconds;
5. if evidence is missing or the state changed, record terminal `BLOCKED` and exit without asking the user or polling;
6. run a broader test, external API check, or repair only when the user makes it a new explicit task;
7. let the terminal ledger event automatically record sanitized routing/memory learning for the bound producer receipt.

First-result latency includes Quick Check and ends at step 2. Ending time is recorded separately and never added to first-result time. The origin returns after linking the new task and states that the delivered result is complete; it does not wait or poll. The Ending task owns only its audit `PASS` or `BLOCKED` result. A tool's own returned state or process exit may be Quick Check evidence for the requested action, but it is not independent Real Verify.

## Persistent End Task Thread

- Create one background Codex task after `CODE READY` or `MAIN RESULT READY`; pass it the lifecycle ID, producer receipt when present, Quick Check evidence, artifact paths, project root, touched files, a read-only mutation boundary, and origin task ID when available.
- Use a saved project with local environment when available; otherwise use a projectless task and absolute paths. Use the configured default model unless an exact model was explicitly requested, and choose proportional reasoning effort.
- Rename the task exactly `End Task-{concise related task name}` with `set_thread_title`, link or identify it, then return the origin immediately with `Delivery: complete; background audit started`.
- The background task—not the returned foreground task—records and reports `PASS` or `BLOCKED` for its audit, finishes within 60 seconds, and never asks the user to resolve an external Git/state change. It must surface its terminal result in its own task or back to the origin when the host supports that.
- If persistent task creation fails, disclose `Background audit unavailable`; never substitute a same-task subagent.

### Required Status Vocabulary

- `MAIN RESULT READY`: producer work is complete, usable, and delivered.
- `PASS`: the short Ending audit recorded sufficient handoff evidence.
- `BLOCKED`: the short audit could not establish evidence (including concurrent state change) and has ended.

Do not describe audit `BLOCKED` as a block on the already-delivered result.

The origin final is complete after result presentation. The End Task thread final requires lifecycle PASS or explicit BLOCKED. No hook is used or installed.

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

Routing quality learning records only the producer pair after Real. The adaptive receipt carries its project/task/module/file/symbol/code context; start the lifecycle with `--producer-receipt`, then the terminal ledger event invokes `obsidian_model_memory.py record` automatically. Obsidian broad `Model Switch.md` pages are the sole active private authority; no local model-learning file or central monthly archive is active. The current catalog may expose Spark as the priority text/code producer at low/high effort; the quality ladder and repair pair use only the highest registered numeric GPT family and switch families when a newer version appears. Operational failures are neutral; a priority-producer correctness/quality failure starts a new quality-pair repair lifecycle. A verifier pair is never recorded as the producer pair, and inline work without a producer receipt never fabricates learning.

## Real Verify Workflow

1. Read the observable acceptance target and the already-presented result.
2. Select one realistic evidence path proportional to risk.
3. Run or inspect the actual artifact/state.
4. Record input, method, observed output, and pass/fail reason.
5. On handoff pass, record lifecycle `PASS`; a bound producer receipt records the producer outcome on the matching broad Obsidian `Model Switch.md` page before terminal PASS.
6. On missing evidence, timeout, or concurrent state change, record lifecycle `BLOCKED` and exit; never ask the user for confirmation or start a repair.
7. A correctness repair is a new explicit user task and receives its own Mini Test plus independent Ending audit.

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

- Never turn Quick Check into a broad test suite or independent acceptance claim.
- Never use a same-task subagent for Ending.
- Never substitute a progress update such as `implementation complete` for the required usable `MAIN RESULT READY` presentation.
- Never launch multiple overlapping verifier/review workers for one lifecycle; one Ending worker owns the audit verdict.
- Never hide task state behind repeated `wait` updates or ask a user to unblock Ending. Report only `PASS` or `BLOCKED` for the audit.
- Verify the user's observable result, not only the attempted method.
- Do not hide uncertainty or a blocked environment.
- Do not claim a model ran without runtime evidence.
- Do not let Ending alter the already-presented result; repair requires a new explicit user task.
- Do not let an optimization implementer verify its own work.
- Do not push, deploy, or send external messages without authorization.

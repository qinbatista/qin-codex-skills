---
name: verify-skill
description: "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify in a separate persistent thread. A producer-side bounded Quick Check may precede code presentation; it is not independent verification."
---

# Verify Skill

Verification has two scopes: user-requested verification as the task itself, and post-result Ending Real Verify. End Task is hard-required. When the result needs verification—code/file changes, bug fixes, generated artifacts, UI/render behavior, integrations, or external actions—Ending must execute a real proportional test against the changed result; a receipt summary alone cannot PASS. Build the plan with `scripts/ending_verification_plan.py`. Give every independent check its own persistent `End Task-{task}-{check}` and select that task's model/effort from its own `0-100` check score. All required checks must PASS. Code producers still apply the bounded Quick Check before presentation; Ending is the independent proof.

When the producer can express acceptance as an exact command, test, API probe, render check, receipt, JSON, exit-code, count, or digest, put the real command in `ending_verification_plan.py plan`. Each Ending worker executes only its assigned `run-check`, preserves stdout/stderr/exit code in evidence, and records PASS only when the command meets its expected result. `ending_evidence_manifest.py` may bind immutable inputs, but validating a manifest never replaces the real test.

Never add a broad verifier before the user's first presentation. After presentation, Ending may run the real proportional unit, integration, API, build, render, visual, or state test required to prove the result. Keep each check focused; do not substitute prose inspection for an executable or observable check when one exists.

A same-task subagent is forbidden for Ending because it keeps the origin task active. Use the host's persistent `create_thread` capability, then `set_thread_title` for the exact title. The global lifecycle authorizes this background task. If persistent task creation is unavailable or fails, record and disclose terminal `BLOCKED` with the exact outer-host handoff; do not silently mark the Ending lifecycle complete, substitute a subagent, or start a wait loop.

When the user explicitly asks for a test, audit, review, replay, or verification as the primary task, that work is the requested result and runs normally on the current model. It does not need a fabricated pre-result verification phase.

## Result-First Boundary

The required order is:

1. producer completes the requested result and, for code, runs one bounded Quick Check;
2. show the result immediately with Quick Check PASS/SKIPPED evidence;
3. classify whether Real Verify is required; when required, build one plan containing the exact real checks and an independent score/model pair per check;
4. write a scored lifecycle receipt, bind `--producer-receipt` when present, then create one persistent `End Task-{task}-{check}` per independent plan check;
5. run each assigned real check and require all checks to PASS;
6. on FAIL, record the exact command, exit code, stdout/stderr, and failure class, then automatically create `Fix Task-{task}-{check}` with that error and the allowed files; after repair, create a fresh Ending task with the same acceptance check;
7. repeat the repair/reverify loop for at most three repair attempts; use BLOCKED only for unavailable infrastructure, external state, timeout, or exhausted repair limit;
8. let every terminal ledger event record local history and let receipt-backed producer PASS/FAIL update Obsidian model learning.

First-result latency includes Quick Check and ends at step 2. Ending time is recorded separately. The origin returns after linking the Ending tasks and does not poll. The lifecycle is verified only when every required check and any repair's fresh recheck PASS; BLOCKED does not count as verified. A tool's own producer-side state may be Quick Check evidence, but independent Ending must observe the completed result again.

## Persistent End Task Thread

- Build a plan with one check object per independent acceptance surface. Separate unit, integration/API, render/visual, and live-state checks when they do not share mutable state.
- Create one persistent task per check; pass lifecycle ID, plan/check ID, exact command, score/band, selected model/effort, receipts, project root, touched files, and allowed repair scope.
- Select quality-ladder roles by check score: small uses `weak_default`, standard `balanced_default`, complex `balanced_complex`, and advanced `frontier_complex`. Spark remains a small-edit producer, not an Ending verifier.
- Run `ending_verification_plan.py run-check`; do not merely summarize prior Quick Check output. Independent safe checks may run concurrently. Shared-state checks remain ordered.
- On failure, record terminal FAIL, create the repair task from `repair_handoff`, and require its new Ending task to rerun the original acceptance command. Never let the failing verifier edit the result itself.
- If persistent task creation fails, record and disclose `BLOCKED: persistent End Task unavailable` plus the exact handoff; never substitute a same-task subagent or treat Ending as complete.

### Required Status Vocabulary

- `MAIN RESULT READY`: producer work is complete, usable, and delivered.
- `PASS`: every required real check observed the expected result.
- `FAIL`: a real check observed a defect and emitted a repair handoff.
- `BLOCKED`: verification or repair could not run because of an external/unavailable condition or the three-attempt limit.

Do not call code verified when the lifecycle is FAIL or BLOCKED.

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

Routing quality learning records only the producer pair after Real. Every lifecycle stores complexity score/band locally. The adaptive receipt carries its project/task/module/file/symbol/code/operation/score-band context; start the lifecycle with `--producer-receipt`, then the terminal ledger event invokes `obsidian_model_memory.py record` automatically. Obsidian broad `Model Switch.md` pages are the sole active private model-learning authority. A small `0-24`, low-risk text/code edit tries Spark-low first. Operational failure is neutral and falls back to the contextual quality pair; Spark correctness/quality failure suppresses Spark for the matching context and upgrades the next matching task. Other quality pairs retain after one Real PASS, downgrade after two, and upgrade after quality FAIL. A verifier pair is never recorded as the producer pair, and inline work without a producer receipt never fabricates learning.

## Real Verify Workflow

1. Read the observable acceptance target and the already-presented result.
2. Select one realistic evidence path proportional to risk.
3. Run or inspect the actual artifact/state.
4. Record input, method, observed output, and pass/fail reason.
5. On handoff pass, record lifecycle `PASS`; a bound producer receipt records the producer outcome on the matching broad Obsidian `Model Switch.md` page before terminal PASS.
6. On missing evidence, timeout, or concurrent state change, record lifecycle `BLOCKED` and exit; never ask the user for confirmation or start a repair.
7. A correctness failure automatically creates a scoped repair task with the exact evidence; the repair receives its own Quick Check and a fresh independent Ending check.

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
- Never combine unrelated independent checks into one vague verifier. One Ending task owns one check; safe independent checks may run concurrently.
- Never hide task state behind repeated waits or ask the user to fix a verified code defect manually. Report `PASS`, `FAIL` with repair handoff, or `BLOCKED` with the exact external reason.
- Verify the user's observable result, not only the attempted method.
- Do not hide uncertainty or a blocked environment.
- Do not claim a model ran without runtime evidence.
- Do not let the failing Ending verifier alter the result. Create a separate repair task, then a fresh verifier task.
- Do not let an optimization implementer verify its own work.
- Do not push, deploy, or send external messages without authorization.

---
name: verify-skill
description: "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify in a separate persistent thread. A producer-side bounded Quick Check may precede code presentation; it is not independent verification."
---

# Verify Skill

Verification has two scopes: user-requested verification as the task itself, and post-result Ending Real Verify. End Task is hard-required. When the result needs verification—code/file changes, bug fixes, generated artifacts, UI/render behavior, integrations, or external actions—Ending must execute a real proportional test against the changed result; a receipt summary alone cannot PASS. Build the plan with `scripts/ending_verification_plan.py`. Give every independent check its own persistent `End Task-{task}-{check}` and select that task's model/effort from its own `0-100` check score. All required checks must PASS. Code producers still apply the bounded Quick Check before presentation; Ending is the independent proof.

When the producer can express acceptance as an exact command, test, API probe, render check, receipt, JSON, exit-code, count, or digest, put the real command in `ending_verification_plan.py plan`. Each Ending worker executes only its assigned `run-check`, preserves stdout/stderr/exit code in evidence, and records PASS only when the command meets its expected result. `ending_evidence_manifest.py` may bind immutable inputs, but validating a manifest never replaces the real test.

Never add a broad verifier before the user's first presentation. After presentation, Ending may run the real proportional unit, integration, API, build, render, visual, or state test required to prove the result. Keep each check focused; do not substitute prose inspection for an executable or observable check when one exists.

A same-task subagent is forbidden for Ending because it keeps the origin task active. Use the host's persistent `create_thread` capability with target `{"type":"projectless"}`, then `set_thread_title` for the exact title. Never attach an End Task or Fix Task to the source project; pass the absolute project root/cwd and allowed files in the worker prompt instead. The global lifecycle authorizes this background task. If persistent task creation is unavailable or fails, record and disclose terminal `BLOCKED` with the exact outer-host handoff; do not silently mark the Ending lifecycle complete, substitute a subagent, or start a wait loop.

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
9. after a worker records durable terminal PASS, it calls `set_thread_archived` with `archived=true` and no thread ID so it archives itself; the archive may terminate the worker turn, so no later final message is required. FAIL and BLOCKED workers remain unarchived. If PASS cleanup cannot be accepted, keep the thread visible and return `BLOCKED: PASS recorded but self-archive unavailable`.

First-result latency includes Quick Check and ends at step 2. Ending time is recorded separately. The origin returns after linking the Ending tasks and does not poll. The lifecycle is verified only when every required check and any repair's fresh recheck PASS; BLOCKED does not count as verified. A tool's own producer-side state may be Quick Check evidence, but independent Ending must observe the completed result again.

## Persistent End Task Thread

- Build a plan with one check object per independent acceptance surface. Separate unit, integration/API, render/visual, and live-state checks when they do not share mutable state.
- Create one persistent task per check; pass lifecycle ID, plan/check ID, exact command, score/band, selected model/effort, receipts, project root, touched files, and allowed repair scope.
- Always create End/Fix tasks as projectless global tasks. Bind their project-root working directory and use project-root-relative paths in prompts; project membership is never used for filesystem access.
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

The origin final is complete after result presentation. After recording lifecycle PASS, the End Task archives itself; that action may terminate the worker turn. FAIL/BLOCKED remains visible and unarchived. No hook is used or installed.

## Result Model Disclosure

Use the compact Result Model Disclosure from `task-analyze-skill/references/route-contract.md` verbatim. Do not expand it into the former repeated model, evidence, previous-model, switch-summary, or reason lines.

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

Routing quality learning records only the producer pair after Real. The adaptive receipt carries its project/task/module/file/symbol/code/operation/score-band context; the terminal ledger event invokes `obsidian_model_memory.py record`, which writes the local routing event first and then projects the same stable event ID to broad Obsidian `Model Switch.md`. Both copies retain outcome reason, attempts, score/band, next pair, and recovery pair and are deduplicated during recommendation. A small `0-24`, low-risk text/code edit tries Spark-low first. Operational failure is quality-neutral; correctness/quality failure upgrades the next matching task. A verifier pair is never recorded as the producer pair, and inline work without a producer receipt never fabricates learning.

## Real Verify Workflow

1. Read the observable acceptance target and the already-presented result.
2. Select one realistic evidence path proportional to risk.
3. Run or inspect the actual artifact/state.
4. Record input, method, observed output, and pass/fail reason.
5. On handoff pass, record lifecycle `PASS`; a bound producer receipt records the producer outcome on the matching broad Obsidian `Model Switch.md` page before terminal PASS.
6. After the PASS event is durable, call `set_thread_archived(archived=true)` on the calling thread. Treat an accepted archive as successful cleanup even when it terminates the turn before a final reply. If self-archive is unavailable, retain the thread and emit explicit BLOCKED cleanup status.
7. On missing evidence, timeout, or concurrent state change, record lifecycle `BLOCKED` and exit unarchived; never ask the user for confirmation or start a repair.
8. A correctness failure automatically creates a projectless scoped repair task with the exact evidence; the repair receives its own Quick Check and a fresh independent Ending check.

## Artifact Guidance

### Code And Scripts

Use syntax/compile/import plus a focused real input/output when proportional. For shared or risky logic, add realistic regressions, error paths, side effects, ordering, or live Unity/runtime evidence. Active code-domain probe authoring uses `code-skill`.

### Skills And Instructions

Check frontmatter, loader limits, referenced files, positive/negative contract scenarios, live task replay, runtime model/effort receipt, stale-name cleanup, and mirror behavior as applicable. Static wording alone does not prove routing behavior.

### UI And Visual Artifacts

Open/render the real artifact; inspect desktop and narrow states, interactions, layout, hierarchy, clipping, readability, consistency, and applicable taste rules. The Mandatory Basic UI Gate in `references/ui-problem-index.md` is blocking for every UI change: shared-frame alignment, one-row-first density, single grouping, aligned additions, stable geometry, and truthful state semantics must all pass or have an explicit accessibility, localization, narrow-viewport, or product-priority reason. Use `references/visual-verification-rubric.md` and `references/ui-problem-index.md`; map the evidence to all six rules instead of returning a generic visual-pass statement.

### Documents And Reports

Parse and render the actual file; inspect page count, required sections, typography, spacing, clipping, tables, hierarchy, and source-backed correctness. Use `references/report-manifest.md` for formal reports.

### Browser, Computer, Automation, And Deployment

Execute the real interaction path, inspect errors and side effects, and confirm final observable state. Production/public actions still require authority before execution; authority is a safety precondition, not verification.

## Obsidian And Optimization

For connected projects or repeated failures, Ending Real reads only the directly related merged local/Obsidian routing history and failure lessons. Missing Obsidian leaves a pending projection; future selection still uses the local receipt-backed event. Save sanitized reasons only; never store secrets or raw private transcripts.

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

Create a formal report only when requested or when evidence is long, visual, comparison-heavy, or repository-required.

## Project Cache Artifact Policy

Before the first Codex-selected project-support write, resolve the authoritative `<project-root>`, inspect `<project-root>/Cache/`, and choose the destination there. All agent-created disposable or supporting artifacts — temporary evidence, test scripts/results/fixtures, debug logs/data, intermediate code, image inspection downloads/renders, generated images, receipts, snapshots, comparisons, and probes — must live only under `<project-root>/Cache/`; redirect any proposed path there before writing. Requested durable project source changes and final deliverables remain in the project's declared source/output paths.

Reuse an existing Cache category and naming scheme; otherwise create `Cache/tests/<task>`, `Cache/debug/<task>`, or `Cache/images/<task>` according to the content. Never deliberately use `~/.codex/cache`, `~/.codex/tmp`, another global cache, a system temporary directory, or an ad hoc project-root `tmp/`, `tests/`, or `work/` for project artifacts. This governs agent-selected destinations, not OS/tool-managed internal temporary files outside agent control.

This applies to every local-machine path, not only Cache paths. Any path written into a Skill, script, source file, configuration, documentation, or command must be project-root-relative or resolved at runtime from a discovered project root. Never hard-code a user-specific POSIX home absolute path or Windows drive-letter absolute path. Command examples state that they run from the project root; code accepts or derives that root and joins relative paths with native path APIs.

Unavoidable machine-specific absolute paths needed only for AI access to project-external resources may exist only in project-root `Cache/cache_path.json`. The registry schema is `{"schema_version": 1, "scope": "ai_only", "paths": {...}}`; every stable key contains `path`, `kind` (`file|directory|application`), and a short `purpose`. It is untracked AI-only local state: project source, runtime, tests, build, CI, package scripts, and shipped configuration must never read, import, or depend on it. Never commit, mirror, or publish it, ensure it is explicitly ignored when `Cache/` is not already ignored, and never store credentials, tokens, secrets, or project business data there.

Look up the registry first and validate the schema, absolute path, declared kind, existence, and readability before use. If an entry is missing or stale, perform one bounded platform-aware discovery, update only that key through a sibling file inside `Cache/`, replace the registry atomically, and preserve unrelated keys. For Obsidian, try verified registry keys first, then `CODEX_OBSIDIAN_VAULT`, then the configured open vault in `obsidian.json`, then one exact bounded search; cache each successful external path. Never copy registered absolute values into Skills, source, documentation, commands, logs, receipts, or memory.

Project `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable project structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to canonical build/verification documentation. Do not write implementation details, task history, logs, receipts, test results, evidence, generated data, temporary notes, dependency walkthroughs, long command blocks, or troubleshooting prose there. Store those details in the owning source, project documentation, or a README inside the relevant Cache area.

When Cache content is reusable, retained, workflow-required, or project-influencing, add one concise registry entry to project-root `AGENTS.md`: the exact Cache-relative path, one-line structural role, owner/source of truth, and retention/version-control status. Link to the owning source or detailed README instead of embedding its commands, dependencies, runbook, or regeneration procedure. Update `AGENTS.md` only when project structure, ownership, a critical entry point, or a hard constraint changes. Important Cache without this concise pointer is incomplete; one-off disposable outputs need no entry. Never delete documented important Cache content without explicit authorization; other cleanup may delete only the current task's named Cache folder or explicitly identified disposable files. Final reports go only to the requested output location.

## Guardrails

- Never turn Quick Check into a broad test suite or independent acceptance claim.
- Never use a same-task subagent for Ending.
- Never substitute a progress update such as `implementation complete` for the required usable `MAIN RESULT READY` presentation.
- Never combine unrelated independent checks into one vague verifier. One Ending task owns one check; safe independent checks may run concurrently.
- Never hide task state behind repeated waits or ask the user to fix a verified code defect manually. Report `PASS`, `FAIL` with repair handoff, or `BLOCKED` with the exact external reason.
- Verify the user's observable result, not only the attempted method.
- Do not hide uncertainty or a blocked environment.
- Do not claim runtime receipt proof without a receipt; display a known assignment with explicit unverified evidence.
- Do not let the failing Ending verifier alter the result. Create a separate repair task, then a fresh verifier task.
- Do not let an optimization implementer verify its own work.
- Do not push, deploy, or send external messages without authorization.

---
name: verify-skill
description: "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify in a separate persistent thread. A producer-side bounded Quick Check may precede code presentation; it is not independent verification."
---

# Verify Skill

Verification has two scopes: user-requested verification as the task itself, and mandatory post-result Ending Real Verify for Ending-required work. A low-risk single-result small task records `intentionally_skipped_simple_task` and has no Ending. Standard/complex/advanced, medium/high-risk, and multi-stage work require an Ending. When the result needs verification—code/file changes, bug fixes, generated artifacts, UI/render behavior, integrations, or external actions—Ending must execute a real proportional test against the changed result; a receipt summary alone cannot PASS. Build one plan with `scripts/ending_verification_plan.py`, keep independent checks distinct inside it, and launch exactly one persistent projectless Ending thread for that task. All required checks must PASS. Code producers still apply the bounded Quick Check before presentation; Ending is the independent proof.

When the producer can express acceptance as an exact command, test, API probe, render check, receipt, JSON, exit-code, count, or digest, put the real command in `ending_verification_plan.py plan`. The one Ending worker executes every saved `run-check`, preserves stdout/stderr/exit code in per-check evidence, and records PASS only when every command meets its expected result. `ending_evidence_manifest.py` may bind immutable inputs, but validating a manifest never replaces the real test.

Never add a broad verifier before the user's first presentation. After presentation, Ending may run the real proportional unit, integration, API, build, render, visual, or state test required to prove the result. Keep each check focused; do not substitute prose inspection for an executable or observable check when one exists.

A same-task subagent is forbidden for Ending because it keeps the origin task active. Each `ending-required` receipt gets one Ending in a separate projectless thread; `intentionally_skipped_simple_task` does not. Capture the immutable origin session before launch: the source Codex thread/session ID, host ID, exact project ID, and project root. Resolve the exact saved project by canonical root, build the launch with `scripts/ending_verification_plan.py create-launches --project-id <resolved-id>`, use the host's persistent `create_thread` capability with target `{"type":"projectless"}`, then acknowledge the returned `threadId`, `hostId`, project ID, and actual Ending pair with `ack-launch`. `audit-launches` must report `end_task_trigger_rate=100%`; a plan/handoff alone is not a launch. The End Task belongs to the global task list and remains visible after every terminal status. A failed check or acceptance mismatch records exact evidence and automatically submits its bounded repair prompt through `codex_app__send_message_to_thread` to that immutable origin session; the source session is the only repair executor and then starts one fresh Ending for the same plan. If the origin session or prompt submission is unavailable, record and disclose terminal `BLOCKED`; do not silently mark the Ending lifecycle complete, create a replacement repair session, substitute a subagent, or start a wait loop.

When the user explicitly asks for a test, audit, review, replay, or verification as the primary task, that work is the requested result and runs normally on the current model. It does not need a fabricated pre-result verification phase.

## Result-First Boundary

The required order is:

1. producer completes the requested result and, for code, runs one bounded Quick Check;
2. show the result immediately with Quick Check PASS/SKIPPED evidence;
3. for every `ending-required` result, build one plan containing the smallest exact real/completion checks; each check keeps its own `0-100` score only to scope risk and evidence, never to select the Ending model;
4. write a scored lifecycle receipt, bind `--producer-receipt` when present, then create exactly one persistent projectless `End Task-{task}`;
5. run the bounded checks in that Ending and require all checks to PASS before one terminal closeout;
6. on FAIL, record the exact command, exit code, stdout/stderr, failure class, and acceptance mismatch when applicable; automatically submit the generated `repair_prompt` through `codex_app__send_message_to_thread` to the immutable origin session with the recorded `threadId` and `hostId`;
7. the origin session reads the original request and current result, repairs only the authorized producer scope, runs Quick Check, presents the corrected result and a new producer receipt, then supplies the failed parent ID through `plan --repair-of-lifecycle-id <id>` or `create-launches --repair-of-lifecycle-id <id>`; the launch builder rejects malformed or conflicting IDs, persists the validated ID in the plan/launch spec, and requires the fresh projectless Ending worker to start its lifecycle with that exact `--repair-of-lifecycle-id <id>`;
8. repeat the source-session repair and fresh-reverification loop for at most three repair attempts; if the source session or prompt submission is unavailable, or the limit is exhausted, record BLOCKED;
9. for a durable result, compare the active Skill/process contract, fresh execution evidence, and bounded effective project-result memory; classify responsibility before any project-memory write, require effective local readback, and require Obsidian readback whenever the vault is available;
10. let every terminal ledger event record local and Obsidian history; only receipt-backed producer PASS/FAIL may update adaptive model learning, while known unreceipted assignments remain non-learning observations. Keep every failed Ending and repair handoff visible; never call `set_thread_archived`, create a replacement fixer, let the verifier edit the result, or expose private chain-of-thought.

First-result latency includes Quick Check and ends at step 2. Ending time is recorded separately. The origin returns after linking the Ending and does not poll. The lifecycle is verified only when every required check and any repair's fresh recheck PASS; BLOCKED does not count as verified. A tool's own producer-side state may be Quick Check evidence, but independent Ending must observe the completed result again.

## Persistent End Task Thread

- Build a plan with one check object per independent acceptance surface, but create exactly one persistent projectless global task for the plan. Pass its lifecycle/plan IDs, exact commands, score/bands, actual Ending pair, receipts, project root, touched files, and allowed repair scope.
- A fresh repair Ending must carry one validated failed-parent lifecycle ID from the saved plan or the `create-launches` flag. If both sources are present they must match. The launch spec and every candidate worker prompt carry the resolved ID, and the worker must pass it unchanged to `ending_task_ledger.py --repair-of-lifecycle-id`; an unlinked replacement root lifecycle is a protocol failure.
- The Ending primary is fixed to `gpt-5.3-codex-spark|xhigh`; check score/band controls proportional scope and classification only. If the host explicitly reports the Spark model, `xhigh` effort, scheduler, or required input modality unavailable, the one approved availability fallback is the current registry floor (`gpt-5.6-luna|low`). Record the approved fallback reason in the launch acknowledgement. Correctness, quality, acceptance, protocol, execution, or timeout failure never changes the Ending model.
- Prefer deterministic commands, render/schema/bounds checks, and already-bound release-report digests so Spark can close quickly. Use Luna-low directly only when the check truly requires semantic image input that Spark cannot accept; never replace a required visual judgment with a false shallow PASS.
- Run every plan item with `ending_verification_plan.py run-check`; do not merely summarize prior Quick Check output and do not repeat an exhaustive release gate that already has a current immutable PASS binding. Independent safe checks may run concurrently inside the one Ending; shared-state checks remain ordered.
- On PASS, perform one terminal routing/classification record, the bounded personal-memory scan, and the sanitized project-change result closeout when the task supplied durable-change memory context. A durable PASS requires effective local readback; an available Obsidian projection must also read back, while an unavailable vault records `projection-pending` for future reconciliation. Process philosophy never becomes result-memory payload.
- On failure or acceptance mismatch, record terminal FAIL, submit `repair_handoff.repair_dispatch` to the immutable origin session, and require that session's new Ending task to rerun the original acceptance command. Never let the failing verifier edit the result itself.
- If persistent task creation fails, record and disclose `BLOCKED: persistent End Task unavailable` plus the exact handoff; never substitute a same-task subagent or treat Ending as complete.

### Required Status Vocabulary

- `MAIN RESULT READY`: producer work is complete, usable, and delivered.
- `PASS`: every required real check observed the expected result.
- `FAIL`: a real check observed a defect and emitted a repair handoff.
- `BLOCKED`: verification or repair could not run because of an external/unavailable condition or the three-attempt limit.

Do not call code verified when the lifecycle is FAIL or BLOCKED.

The origin final is complete after result presentation and real End Task launch acknowledgement. The End Task remains visible after PASS/FAIL/BLOCKED. No hook is used or installed.

## Per-Submission Personal Memory Scan

Every Ending-required user submission gets one bounded memory-relevance scan inside its mandatory Ending. A low-risk single-result small task records no Ending memory candidate. The scan is separate from adaptive model routing and project-change memory. It may produce candidates only for durable user preferences, repeated user corrections, or verified technical working patterns that are directly supported by the current submission; it must not infer sensitive traits or persist raw prompts, raw results, private reasoning, machine paths, secrets, or thread/session identifiers.

If the scan finds no candidate, it is a strict no-op for preference memory: do not create a candidate file and do not write a preference-memory event; the same Ending still performs its assigned checks plus routing classification and terminal record closeout. If it finds a candidate, the Ending worker writes an optional project-relative JSON file and passes `--memory-candidates-file <relative-path>` to `ending_task_ledger.py event`. The accepted schema is `{\"candidates\":[...]}` with bounded `kind`, `area`, `basis`, `confidence`, `source=ending`, `statement`, and `evidence` fields.

The personal-memory bridge validates the candidate again, writes one root-first `AI Memory/events.jsonl` memory event, and updates the stable Preferences owner page (`UI Style Preferences.md` for UI candidates when present, otherwise `AI Captured Preferences.md`). If Obsidian is unavailable, it queues only the sanitized candidate bundle locally for replay. A memory write never changes the requested result; an empty candidate set never writes anything.

## Project Result Memory Consistency

Skills and `AGENTS.md` constrain the work process; project-change memory stores only sanitized, verified outcomes. They are separate authorities and neither may impersonate the other. Model-routing memory, personal preference memory, and project-result memory are also three independent flows: one flow's successful write, pending projection, or no-op never satisfies another flow.

The producer marks the plan `project_memory_closeout.mode=durable` only for durable project-file changes and supplies sanitized module, scope, change kind, outcome summary/reason/result, project-relative files, and code symbols where required. All other tasks use `mode=none`; they create no project-result consistency file and the ledger records a non-persistent no-op.

Before a durable terminal event, Ending reads the active process contract, every fresh bounded execution result, and only the related effective project-memory records. It writes one project-relative schema-1 consistency file and passes `--memory-consistency-file` to `ending_task_ledger.py event`. The file contains `classification`, `process_status`, `execution_status`, `memory_status`, `action`, and a bounded sanitized `evidence` list. The only classifications and actions are:

- `aligned` or `no_prior_memory`: process and execution PASS; append the current verified result once with `action=record`.
- `memory_record_defect`: process and execution PASS but the effective result record is wrong; append one `action=correction` record with `supersedes`. Never rewrite or delete the old event.
- `memory_projection_defect`: the correct local result exists but its Obsidian projection is missing or mismatched; use `action=reconcile` for that `record_id` without creating another semantic result.
- `skill_contract_defect`: fresh evidence shows the process contract itself is wrong; terminal FAIL with `action=origin_repair` and send the evidence to the immutable origin. Ending never edits the Skill.
- `execution_drift`: the process contract is correct but the producer did not follow it; terminal FAIL with `action=origin_repair`. Never rewrite result memory to conceal the drift.
- `insufficient_evidence`: one of the three authorities is unavailable or cannot be distinguished; terminal BLOCKED with `action=blocked`, never PASS.

For `aligned`, `no_prior_memory`, `memory_record_defect`, and `memory_projection_defect`, the ledger invokes `project_change_memory.py` and performs a bounded effective-record readback. When Obsidian is available, its projection receipt must report `read_back_verified=true`; an available-but-unverified projection keeps the final gate closed. When Obsidian is unavailable, the verified local record remains authoritative, PASS records `projection-pending`, and the next bounded task entry retries reconciliation before relying on the projection. Subsequent recall reads effective memory only, so a superseded incorrect record cannot win over its correction.

## Result Model Disclosure

Use the compact Result Model Disclosure from `task-analyze-skill/references/route-contract.md` verbatim. Do not expand it into the former repeated model, evidence, previous-model, switch-summary, or reason lines. A composite final additionally includes the generated `Model stages (N):` block so the verifier's own score/pair/status is visible beside every result stage.

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

Routing quality learning records only the receipt-backed producer pair after Real. The terminal ledger always writes a project/task model event locally and projects the same stable event ID to the matching native Obsidian category page. When the adaptive receipt exists, it supplies project/task/module/file/symbol/code/operation/score-band context and may move the route. Without it, a known Ending assignment is recorded with `learning_eligible=false`, retains its pair, and cannot count toward PASS descent or FAIL ascent. The compact Model Switch and shared-category backlinks are refreshed around that page. Both authorities retain outcome reason, attempts, score/band, next pair, and recovery pair and are deduplicated during recommendation. A verifier pair is never mislabeled as the producer pair, and inline work never fabricates a receipt.

## Real Verify Workflow

1. Read the observable acceptance target and the already-presented result.
2. Select one realistic evidence path proportional to risk.
3. Run or inspect the actual artifact/state.
4. Record input, method, observed output, and pass/fail reason.
5. On handoff pass, record lifecycle `PASS`; a bound producer receipt records the producer outcome on the matching native Obsidian category page before terminal PASS.
6. After any terminal event, keep the calling project task visible and print the structured `model_assessment`; never auto-archive or delete it.
7. On missing evidence, timeout, or concurrent state change, record lifecycle `BLOCKED` and exit visible; never ask the user for confirmation or start a repair.
8. A correctness failure or acceptance mismatch automatically submits a scoped repair prompt to the immutable origin session with the exact evidence; that session receives the original request context, runs Quick Check, presents the corrected result, and starts a fresh independent Ending check. Repeat for at most three repairs; missing or failed prompt submission is BLOCKED.

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

Optimization verification is independent Ending Real. Require different optimizer/verifier identities, raw before/after inputs and outputs, same-behavior acceptance, and dependency/order/side-effect/error checks. For adaptive routing, verify primary steady selected-execution tokens/time separately from actual first-result wait, route/controller overhead, calibration failures, retries/fallbacks/repairs, entry probes, and Ending. Require both Luna-max and Sol-ultra entry probes to return the exact result and same stable route/capability assignment. If no independent verifier is callable, report it as blocked; do not self-certify.

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

This applies to every local-machine path, not only Cache paths. Skills, scripts, source, configuration, documentation, and commands use project-root-relative paths or resolve them at runtime from a discovered project root. Never hard-code a user-specific POSIX home absolute path or Windows drive-letter absolute path. Command examples state that they run from the project root; code accepts or derives that root and joins relative paths with native path APIs.

Unavoidable machine-specific absolute paths needed only for AI access to project-external resources may exist only in project-root `Cache/cache_path.json`. The registry schema is `{"schema_version": 1, "scope": "ai_only", "paths": {...}}`; every stable key contains `path`, `kind` (`file|directory|application`), and a short `purpose`. It is untracked AI-only local state: project source, runtime, tests, build, CI, package scripts, and shipped configuration must never read, import, or depend on it. Never commit, mirror, or publish it, ensure it is explicitly ignored when `Cache/` is not already ignored, and never store credentials, tokens, secrets, or project business data there.

Look up the registry first and validate the schema, absolute path, declared kind, existence, and readability before use. If an entry is missing or stale, perform one bounded platform-aware discovery, update only that key through a sibling file inside `Cache/`, replace the registry atomically, and preserve unrelated keys. For Obsidian, try verified registry keys first, then `CODEX_OBSIDIAN_VAULT`, then the configured open vault in `obsidian.json`, then one exact bounded search; cache each successful external path. Never copy registered absolute values into Skills, source, documentation, commands, logs, receipts, or memory.

Project `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable project structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to canonical build/verification documentation. Do not write implementation details, task history, logs, receipts, test results, evidence, generated data, temporary notes, dependency walkthroughs, long command blocks, or troubleshooting prose there. Store those details in the owning source, project documentation, or a README inside the relevant Cache area.

When Cache content is reusable, retained, workflow-required, or project-influencing, add one concise registry entry to project-root `AGENTS.md`: the exact Cache-relative path, one-line structural role, owner/source of truth, and retention/version-control status. Link to the owning source or detailed README instead of embedding its commands, dependencies, runbook, or regeneration procedure. Update `AGENTS.md` only when project structure, ownership, a critical entry point, or a hard constraint changes. Important Cache without this concise pointer is incomplete; one-off disposable outputs need no entry. Never delete documented important Cache content without explicit authorization; other cleanup may delete only the current task's named Cache folder or explicitly identified disposable files. Final reports go only to the requested output location.

## Guardrails

- Never turn Quick Check into a broad test suite or independent acceptance claim.
- Never use a same-task subagent for Ending.
- Never substitute a progress update such as `implementation complete` for the required usable `MAIN RESULT READY` presentation.
- Never collapse distinct checks into one vague assertion. One Ending task owns the task's explicit check list; safe checks may run concurrently and shared-state checks stay ordered.
- Never hide task state behind repeated waits or ask the user to fix a verified code defect manually. Report `PASS`, `FAIL` with repair handoff, or `BLOCKED` with the exact external reason.
- Verify the user's observable result, not only the attempted method.
- Do not hide uncertainty or a blocked environment.
- Do not claim runtime receipt proof without a receipt; display a known assignment with explicit unverified evidence.
- Do not let the failing Ending verifier alter the result. Submit the exact bounded repair prompt to the immutable origin session, then require that source session to start a fresh verifier task.
- Do not let an optimization implementer verify its own work.
- Do not push, deploy, or send external messages without authorization.

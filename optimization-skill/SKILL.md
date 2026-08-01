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
- Same-behavior Real Verify, token/time comparison, broad regression, and independent optimization verification run after the main result when genuinely required. Inline execution may call a different verifier directly; an admitted route uses Ending Task.
- Do not call the optimization independently verified until the different verifier passes. If it fails, notify the user and reopen the task.

## Model Contract

Eligible optimization production follows the catalog-generated shared ladder and matching Obsidian context. An admitted optimization node follows the exact model and effort in the locked plan:

- Shared role models are cold-start hints only; auto-build or refresh the highest registered numeric GPT family from weakest to strongest and exclude older families from active switching.
- Every Python/C#/Unity C# helper or implementation node still loads `code-skill`. Eligible small low-risk edits try Spark first; other production executes the saved contextual quality pair. Two Real PASS results permit one-rung descent and verified correctness/quality failure moves one rung up. Spark failure suppresses the matching score band and upgrades the next task. Spark remains available for admitted disjoint source branches.
- Correctness and quality are eligibility gates. Rank tokens, then process time, then weaker rung only when every compared Real-passing pair shares the same exact workload hash with complete metrics; otherwise use the quality boundary.
- A frozen exact-profile pair is reused until verified failure or material ladder, hard-floor, profile, or policy drift.

An admitted node does not silently inherit or reselect another pair. Ineligible inline work does not fabricate a receipt. A label is not execution proof; eligible production and any claimed model routing, benchmark, or savings require the matched runtime receipt.

## Workflow

1. Identify the owning skill/process and observable behavior to preserve.
2. Capture raw before input, method, output, tokens/time when relevant, order, side effects, and failure behavior.
3. Select the smallest reusable form: tighter rule, reference, script, asset, template, or safe parallel topology.
4. Use `code-skill` for every Python/C# implementation or authored probe.
5. Implement only the authorized optimization.
6. Show the raw after artifact immediately; do not add a foreground verifier.
7. After presentation, start Ending with the producer receipt when one exists, then hand the before/after evidence to an independent global projectless Ending Real verifier without changing the locked route. PASS records durable evidence then self-archives; FAIL/BLOCKED stays visible.
8. When independent proof is required, hand optimizer identity, files, commands, before/after evidence, and remaining risks to a different verifier after the main result.

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
- Do not create new global skills unless the user explicitly authorizes that global skill change.

### Project Cache Artifact Policy

Before the first Codex-selected project-support write, resolve the authoritative `<project-root>`, inspect `<project-root>/Cache/`, and choose the destination there. All agent-created disposable or supporting artifacts — temporary evidence, test scripts/results/fixtures, debug logs/data, intermediate code, image inspection downloads/renders, generated images, receipts, snapshots, comparisons, and probes — must live only under `<project-root>/Cache/`; redirect any proposed path there before writing. Requested durable project source changes and final deliverables remain in the project's declared source/output paths.

Reuse an existing Cache category and naming scheme; otherwise create `Cache/tests/<task>`, `Cache/debug/<task>`, or `Cache/images/<task>` according to the content. Never deliberately use `~/.codex/cache`, `~/.codex/tmp`, another global cache, a system temporary directory, or an ad hoc project-root `tmp/`, `tests/`, or `work/` for project artifacts. This governs agent-selected destinations, not OS/tool-managed internal temporary files outside agent control.

This applies to every local-machine path, not only Cache paths. Any path written into a Skill, script, source file, configuration, documentation, or command must be project-root-relative or resolved at runtime from a discovered project root. Never hard-code a user-specific POSIX home absolute path or Windows drive-letter absolute path. Command examples state that they run from the project root; code accepts or derives that root and joins relative paths with native path APIs.

Unavoidable machine-specific absolute paths needed only for AI access to project-external resources may exist only in project-root `Cache/cache_path.json`. The registry schema is `{"schema_version": 1, "scope": "ai_only", "paths": {...}}`; every stable key contains `path`, `kind` (`file|directory|application`), and a short `purpose`. It is untracked AI-only local state: project source, runtime, tests, build, CI, package scripts, and shipped configuration must never read, import, or depend on it. Never commit, mirror, or publish it, ensure it is explicitly ignored when `Cache/` is not already ignored, and never store credentials, tokens, secrets, or project business data there.

Look up the registry first and validate the schema, absolute path, declared kind, existence, and readability before use. If an entry is missing or stale, perform one bounded platform-aware discovery, update only that key through a sibling file inside `Cache/`, replace the registry atomically, and preserve unrelated keys. For Obsidian, try verified registry keys first, then `CODEX_OBSIDIAN_VAULT`, then the configured open vault in `obsidian.json`, then one exact bounded search; cache each successful external path. Never copy registered absolute values into Skills, source, documentation, commands, logs, receipts, or memory.

Project `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable project structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to canonical build/verification documentation. Do not write implementation details, task history, logs, receipts, test results, evidence, generated data, temporary notes, dependency walkthroughs, long command blocks, or troubleshooting prose there. Store those details in the owning source, project documentation, or a README inside the relevant Cache area.

When Cache content is reusable, retained, workflow-required, or project-influencing, add one concise registry entry to project-root `AGENTS.md`: the exact Cache-relative path, one-line structural role, owner/source of truth, and retention/version-control status. Link to the owning source or detailed README instead of embedding its commands, dependencies, runbook, or regeneration procedure. Update `AGENTS.md` only when project structure, ownership, a critical entry point, or a hard constraint changes. Important Cache without this concise pointer is incomplete; one-off disposable outputs need no entry. Never delete documented important Cache content without explicit authorization; other cleanup may delete only the current task's named Cache folder or explicitly identified disposable files.

## Guardrails

- Do not optimize before the requested base behavior exists.
- Do not move reasoning-heavy judgment into brittle code.
- Do not parallelize shared-state, ordered, Unity main-thread, or side-effect-heavy work without proof.
- Do not push/publish unless explicitly authorized.
- Do not wait to show the completed result for Ending Task comparison.

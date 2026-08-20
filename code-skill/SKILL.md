---
name: code-skill
description: "Do not use for an exact-scoped read-only lookup, audit, transform, or workflow reconstruction with no requested output artifact, or in the observable entry parent before adaptive dispatch. The selected result producer or positively admitted node loads this skill as the universal before/during-writing process gate for every code creation, repair, feature, refactor, or test-writing task in any programming language, including when another Skill owns implementation. Every Unity game C# writing node must also load the global Unity Game Code Structure Design reference; a project may tighten that Controller/Manager/ScriptableObject contract but cannot silently weaken it. In registered domains, this skill also owns implementation, edit, execution, debug, refactor, authored tests/probes, and domain reasoning beyond supplied scope."
---

# Code Skill

Use this as the global executor for active registry-owned code work that needs domain behavior or style rules. The entry parent dispatches first without loading this file; the selected `LOCKED_ROUTE_NODE` result producer loads it. Every submission and every dynamic code segment receives a deterministic `0-100` complexity score. A low-risk, low-ambiguity code, write, probe, command, transform, or execute segment scoring `0-24` runs the same-session outcome gate, then tries the catalog priority producer only with no stronger session route, even inside a larger task; other eligible implementations execute their score role or Obsidian-context quality pair. A self-contained bounded read-only lookup or audit stays on the bootstrap only when it requests no file/report; any requested output artifact is producer work. The producer performs one bounded Quick Check before presenting code; deeper independent verification runs later in a separate persistent Ending thread.

## Internal Route Selection

### Required Scope

Load this skill as the process gate for every inline request or admitted node that creates, repairs, extends, refactors, or writes tests for code in any programming language. When another domain Skill owns implementation, apply `references/code-writing-philosophy.md` before and during writing while leaving execution ownership with that Skill.

In active registry-owned code domains, also use this skill as the executor for work that writes, debugs, refactors, tests, authors probes, or needs domain-specific explanation, including:

- Python;
- C# or Unity C#;
- prompts embedded in Python/C# executable behavior;
- Python/C# helper scripts used by another skill;
- Python/C# optimization implementation.

For every code creation, repair, feature, refactor, or test-writing node, including a small edit, read and follow `references/code-writing-philosophy.md` before and during writing. It is mandatory process authority; an exact-scoped read-only lookup stays outside this gate.

Use this skill's executor and language-specific references only for the registered domain resolved from the inline request or admitted node; other production language domains retain their owning production Skill while still using the universal philosophy gate.

Do not load it for an exact bounded read-only source lookup/audit that supplies its source scope and output contract and requests no output artifact. The bootstrap collects that evidence once and returns. A Cache note or report is an artifact and must be produced through the adaptive runner.

## Execution-domain routing

| Work | `execution_domain` | Rules |
|---|---|---|
| Python | `python` | `references/python-rules.md` |
| Plain non-Unity C# | `csharp` | `references/csharp-rules.md` |
| Unity C# | `unity_csharp` | `references/csharp-rules.md`, `references/unity-csharp-rules.md`, then `references/unity-game-code-structure-design.md` for game runtime code |
| Legacy code with no domain | `code_unspecified` | migration/history-only; do not use for new work |

Any new active code domain is registry-owned by `routing_policy.py::EXECUTION_DOMAINS` and follows the [extension guide](../task-analyze-skill/references/router-extension-guide.md). Do not infer a new domain from a similar name.

## References

Read only what the inline request or admitted node needs:

- literal read-only source lookups on the one-call path: no language or coding reference; the request or admitted node supplies the exact owner path, source allowlist, output contract, and deterministic acceptance target;
- every code-writing node: `references/code-writing-philosophy.md`;
- all non-trivial code: `references/coding-approach.md`;
- any registered-domain change that affects rendered UI, layout, controls, styling, editor chrome, runtime HUD, or user-facing UI information: load `references/coding-approach.md` and apply its Mandatory Basic UI Change Gate and User Experience Philosophy before editing;
- Python: `references/python-rules.md`;
- plain C#: `references/csharp-rules.md`;
- Unity C#: `references/csharp-rules.md` and `references/unity-csharp-rules.md`; every Unity game C# create/edit/repair/refactor/test node also reads `references/unity-game-code-structure-design.md` after the nearest project `AGENTS.md` and before selecting an ownership pattern;
- prompt-in-code: always load the global `prompt-skill` first, then use `references/prompt-generation.md` for executable-string and language-specific details; a missing or skipped `prompt-skill` is a prompt-task routing failure, not a fallback condition;
- code or commands that may execute on a developer or host operating system: load the global `cross-platform-execution` skill before editing, classify the project execution boundary, and apply its platform contract;
- safe repeated/parallel registered-code work: `references/parallelization.md`;
- active catalog-derived priority-producer boundary and legacy parsing notes: `references/spark-small-code.md`.

Active registry-owned code domains share this executor while retaining separate evidence keys and references. Current examples are `python`, `csharp`, and `unity_csharp`; `code_unspecified` is migration/history-only. Registry metadata identifies the domain; language rules are documented in this skill's `references` directory (for example, `python-rules.md`, `csharp-rules.md`, and `unity-csharp-rules.md`).

For prompt-in-code work, use `Prompt idea -> Prompt goal -> observed problems -> smallest complete solution` as an internal reasoning checklist, inspect the existing prompt and validators, and apply the complete `prompt-skill` contract plus only the conditional controls that materially improve behavior before the language-specific reference. Do not show a planning preamble; apply the Quick Check boundary below before presenting the completed change.

### Platform compatibility for Skill runtime code

When this skill task writes functional code in a Skill’s runtime surface (`scripts`, `bin`, `tools`), route platform compatibility through the Skill platform contract and require checker execution before publish- or mirror-style completion.

### Platform compatibility for project code

For project scripts, CLIs, setup commands, build/deploy helpers, and developer tooling, use `cross-platform-execution` to decide the runtime boundary before implementation. Default host-run behavior to Windows, macOS, and Linux. Keep genuine platform differences in one explicit runtime dispatch instead of writing a macOS path first and leaving other platforms implicit.

Do not add host branches inside a declared managed runtime merely because its repository can be checked out on multiple hosts. Examples include code that runs only inside a Linux container, Unity runtime/editor code that uses Unity APIs, and a service deployed only to a fixed server image. Apply portability to the host-side commands that enter those runtimes.

## Model Contract

- Adaptive code work reads the catalog-generated quality contract and the bounded native Obsidian route for matching project/task/module/file/symbol/code context: current category, shared category, and exact-fingerprint linked project categories. Score bands are `0-24` small, `25-49` standard, `50-74` complex, and `75-100` advanced. One Real PASS retains a quality pair, two PASS results downgrade one rung, and quality FAIL upgrades one rung.
- A low-risk, low-ambiguity text/code/write/execute node in the small band runs the same-session outcome gate first and tries Spark only with no stronger session route, based on its own node score rather than the parent task score. This includes dependency-ready downstream nodes. A zero-result, zero-token Spark operational failure may immediately use the node's quality fallback. An Ending correctness/quality failure suppresses Spark for the matching project/task/operation/code-kind/score-band context and upgrades the next matching task to the quality pair. Spark remains available for fixed disjoint-source schedule branches.
- Old local `model_experience.json` remains legacy read-only. Every adaptive code profile retains `code-skill` ownership; Obsidian selects within the highest registered numeric GPT family and learns its verified boundary. Older numeric families remain catalog-only.
- An admitted fallback must already be allowed by Task Analyze and must carry its runtime reroute/receipt evidence. Inline execution does not invent fallback metadata.
- Image-dependent, broad integration, or evidence-heavy work uses a balanced/frontier cold start inside that highest family; verified bounded work descends only within the active family and its efforts.
- A planned label is not execution proof. Return receipt evidence only when an admitted route, explicit benchmark, or routing acceptance target requires it.

## Workflow

1. Confirm the request or dynamic node names an active registered code domain and `code-skill`; retain its own score, band, pair, dependencies, purpose, and stop condition.
2. Read `references/code-writing-philosophy.md`, the relevant references, and existing source; make its explicit ownership, lifecycle-performance, and `AGENTS.md` continuity decisions before editing.
3. Resolve important assumptions internally and choose the smallest viable design; ask only when a missing choice genuinely blocks safe implementation.
4. Preserve Qin's existing style, naming, structure, and unrelated user changes.
5. For UI-affecting code or user-facing UI information, enforce the six-rule UI gate and User Experience Philosophy before implementation; preserve any intentional exception as an explicit responsive, accessibility, localization, or product-priority decision.
6. Keep Python signatures, calls, and literals on one line when the project/global rules require that style; for Unity C#, keep constructor calls and collection entries flat on one physical line unless wrapping is explicitly requested.
7. Implement only the requested behavior; avoid unrequested abstractions, features, fallbacks, or compatibility layers.
8. Complete the philosophy's lifecycle performance pass and confirm the `AGENTS.md` continuity decision, then run exactly one producer-side Quick Check. For light/local code, use the smallest safe smoke that exercises the changed function or direct path. For UI-affecting code, confirm only that the changed source expresses the intended alignment/container/responsive contract; rendered proof belongs to Ending. For external-API, large-file, expensive-build, destructive, or side-effect-heavy work, do not execute the heavy path; check syntax plus the changed function, variable, import, and direct-reference names without importing code that may trigger side effects. Do not add a broad suite, full build, full lint, UI/visual pass, log cleanup, repeated source review, or independent acceptance before presentation.
9. Present `CODE READY` with changed paths, concrete behavior, the complete Result Model Disclosure block, and `Quick Check: PASS` or `Quick Check: SKIPPED (heavy) — <static evidence>`. Quick Check time is included in first-result latency.
10. Start the lifecycle ledger and bind the producer or aggregate graph receipt when present. A successful durable code change normally exposes `real_test` through its Quick Check and is Ending-required; a no-surface result records `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_update`. Capture the immutable origin session before launch, then build the smallest real-test plan with `verify-skill/scripts/ending_verification_plan.py` and create exactly one global projectless `End Task-{task}`. Invoke only the generated `create_thread` target `{"type":"projectless"}`; keep the origin project as execution context only. Require `codex_app__list_threads` readback with `projectId=null` or absent before acknowledgement. Project/current-task/same-task-subtask placement is BLOCKED. The Ending controller stays fixed `gpt-5.3-codex-spark|xhigh`; explicit primary availability failure permits only registry-floor `gpt-5.6-luna|low`. It runs deterministic checks directly and may delegate saved semantic runtime, code-quality, prompt, UI, or visual checks to capability-routed Terra/Sol `ENDING_CHECK_WORKER` nodes. Those nodes read every listed Skill, run one saved check, write fresh evidence, and never edit producer files or own routing, lifecycle, repair, or terminal records. Correctness, quality, protocol, execution, timeout, or acceptance failure never changes the Spark controller. All checks must PASS before one terminal closeout. FAIL returns exact evidence through `codex_app__send_message_to_thread` to the immutable origin, which repairs, runs one Quick Check, presents again, and starts a fresh Spark-first global projectless Ending with `--repair-of-lifecycle-id`, for up to three attempts. Never emulate task creation, wait for Ending in the origin, self-repair in verification, or create another End/Fix lifecycle.

The smallest safe syntax, existence, direct-reference, or focused local execution check belongs to producer Quick Check. Full builds, broad lint, integration/API calls, large-file processing, live side effects, and regressions belong to the detached Ending thread unless they are themselves the user's requested task.

## Result Model Disclosure

Use the compact Result Model Disclosure from `task-analyze-skill/references/route-contract.md` verbatim. Do not expand it into the former repeated model, evidence, previous-model, switch-summary, or reason lines.

The post-result Ending lifecycle runs whenever the released result has a `real_test`, `information_update`, or `memory_update` surface; code normally supplies `real_test` through Quick Check. Return published code after exactly one Quick Check, state that the independent Ending has started, and do not poll it. Spark remains the Ending controller even when capability-routed Terra/Sol check workers provide semantic evidence. A failing check records exact evidence and submits the repair prompt to the immutable source session; the repaired code gets a fresh Spark-first Ending. Only a receipt-backed producer event may change producer routing; controller and check-worker assignments are observation-only.

## Optimization Boundary

When optimization is explicitly requested or admitted, implement only the authorized change and return raw before/after inputs, outputs, token/time evidence when relevant, and known risks. The optimization implementer never self-certifies same behavior. A different `verify-skill` worker performs independent verification after the result; an admitted route may schedule that worker in Ending Task.

When optimization is not the requested result, report a discovered candidate instead of silently expanding scope. An admitted route may place it in Ending Task; inline work does not create background work merely to record the idea.

## Generated File Placement

### Project Cache Artifact Policy

Before the first Codex-selected project-support write, resolve the authoritative `<project-root>`, inspect `<project-root>/Cache/`, and choose the destination there. All agent-created disposable or supporting artifacts — temporary or intermediate code, test scripts/results/fixtures, logs, receipts, debug data, image inspection downloads/renders, generated images, snapshots, comparisons, and probes — must live only under `<project-root>/Cache/`; redirect any proposed path there before writing. Requested durable project source changes and final deliverables remain in the project's declared source/output paths.

Reuse an existing Cache category and naming scheme; otherwise create `Cache/tests/<task>`, `Cache/debug/<task>`, or `Cache/images/<task>` according to the content. Never deliberately use `~/.codex/cache`, `~/.codex/tmp`, another global cache, a system temporary directory, or an ad hoc project-root `tmp/`, `tests/`, or `work/` for project artifacts. This governs agent-selected destinations, not OS/tool-managed internal temporary files outside agent control.

This applies to every local-machine path, not only Cache paths. Any path written into a Skill, script, source file, configuration, documentation, or command must use project-root-relative paths or resolve them at runtime from a discovered project root. Never hard-code a user-specific POSIX home absolute path or Windows drive-letter absolute path. Command examples state that they run from the project root; code accepts or derives that root and joins relative paths with native path APIs.

Unavoidable machine-specific absolute paths needed only for AI access to project-external resources may exist only in project-root `Cache/cache_path.json`. The registry schema is `{"schema_version": 1, "scope": "ai_only", "paths": {...}}`; every stable key contains `path`, `kind` (`file|directory|application`), and a short `purpose`. It is untracked AI-only local state: project source, runtime, tests, build, CI, package scripts, and shipped configuration must never read, import, or depend on it. Never commit, mirror, or publish it, ensure it is explicitly ignored when `Cache/` is not already ignored, and never store credentials, tokens, secrets, or project business data there.

Look up the registry first and validate the schema, absolute path, declared kind, existence, and readability before use. If an entry is missing or stale, perform one bounded platform-aware discovery, update only that key through a sibling file inside `Cache/`, replace the registry atomically, and preserve unrelated keys. For Obsidian, try verified registry keys first, then `CODEX_OBSIDIAN_VAULT`, then the configured open vault in `obsidian.json`, then one exact bounded search; cache each successful external path. Never copy registered absolute values into Skills, source, documentation, commands, logs, receipts, or memory.

Project `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable project structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to canonical build/verification documentation. Do not write implementation details, task history, logs, receipts, test results, evidence, generated data, temporary notes, dependency walkthroughs, long command blocks, or troubleshooting prose there. Store those details in the owning source, project documentation, or a README inside the relevant Cache area.

When Cache content is reusable, retained, workflow-required, or project-influencing, add one concise registry entry to project-root `AGENTS.md`: the exact Cache-relative path, one-line structural role, owner/source of truth, and retention/version-control status. Link to the owning source or detailed README instead of embedding its commands, dependencies, runbook, or regeneration procedure. Update `AGENTS.md` only when project structure, ownership, a critical entry point, or a hard constraint changes. Important Cache without this concise pointer is incomplete; one-off disposable outputs need no entry. Never delete documented important Cache content without explicit authorization; other cleanup may delete only the current task's named Cache folder or explicitly identified disposable files.

## Guardrails

- Preserve execution order, side effects, exception behavior, Unity main-thread rules, and public contracts unless the request changes them.
- Do not parallelize order-sensitive or shared-state code without an authorized plan and independent comparison.
- Do not claim independent Real Verify before the different verifier completes.
- Do not push or publish unless explicitly authorized.

---
name: code-skill
description: "Do not use for an exact-scoped read-only lookup, audit, transform, or workflow reconstruction, or in the Sol-ultra entry parent before adaptive dispatch. The selected result producer or positively admitted node loads this skill for code implementation, edit, execution, debug, refactor, authored tests/probes, or domain reasoning beyond supplied scope."
---

# Code Skill

Use this as the global executor for active registry-owned code work that needs domain behavior or style rules. The Sol-ultra entry parent dispatches first without loading this file; the selected `LOCKED_ROUTE_NODE` result producer loads it. Every submission receives a deterministic `0-100` complexity score. A low-risk, low-ambiguity text/code edit scoring `0-24` tries the catalog priority producer first; other eligible implementations execute the Obsidian-context catalog-derived quality pair. A self-contained bounded read-only lookup or audit stays on the bootstrap but still reports its score. Full Task Analyze may also deliver an exact locked code node. The producer performs one bounded Quick Check before presenting code; deeper independent verification runs later in a separate persistent Ending thread.

## Internal Route Selection

### Required Scope

Load this skill for every inline request or admitted node that writes, debugs, refactors, tests, authors probes, or needs domain-specific explanation in an active registry-owned code domain, including:

- Python;
- C# or Unity C#;
- prompts embedded in Python/C# executable behavior;
- Python/C# helper scripts used by another skill;
- Python/C# optimization implementation.

Use only the registered domain resolved from the inline request or admitted node; other production language domains remain with their owning production skill until explicitly registered here.

Do not load it for an exact bounded read-only source lookup/audit that already supplies its source scope and output contract. The bootstrap collects that evidence once and returns.

## Execution-domain routing

| Work | `execution_domain` | Rules |
|---|---|---|
| Python | `python` | `references/python-rules.md` |
| Plain non-Unity C# | `csharp` | `references/csharp-rules.md` |
| Unity C# | `unity_csharp` | `references/csharp-rules.md` then `references/unity-csharp-rules.md` |
| Legacy code with no domain | `code_unspecified` | migration/history-only; do not use for new work |

Any new active code domain is registry-owned by `routing_policy.py::EXECUTION_DOMAINS` and follows the [extension guide](../task-analyze-skill/references/router-extension-guide.md). Do not infer a new domain from a similar name.

## References

Read only what the inline request or admitted node needs:

- literal read-only source lookups on the one-call path: no language or coding reference; the request or admitted node supplies the exact owner path, source allowlist, output contract, and deterministic acceptance target;
- all non-trivial code: `references/coding-approach.md`;
- Python: `references/python-rules.md`;
- plain C#: `references/csharp-rules.md`;
- Unity C#: `references/csharp-rules.md` and `references/unity-csharp-rules.md`;
- prompt-in-code: always load the global `prompt-skill` first, then use `references/prompt-generation.md` for executable-string and language-specific details; a missing or skipped `prompt-skill` is a prompt-task routing failure, not a fallback condition;
- safe repeated/parallel registered-code work: `references/parallelization.md`;
- active catalog-derived priority-producer boundary and legacy parsing notes: `references/spark-small-code.md`.

Active registry-owned code domains share this executor while retaining separate evidence keys and references. Current examples are `python`, `csharp`, and `unity_csharp`; `code_unspecified` is migration/history-only. Registry metadata identifies the domain; language rules are documented in this skill's `references` directory (for example, `python-rules.md`, `csharp-rules.md`, and `unity-csharp-rules.md`).

For prompt-in-code work, use `Prompt idea -> Prompt goal -> observed problems -> smallest complete solution` as an internal reasoning checklist, inspect the existing prompt and validators, and apply the complete `prompt-skill` contract plus only the conditional controls that materially improve behavior before the language-specific reference. Do not show a planning preamble; apply the Quick Check boundary below before presenting the completed change.

## Model Contract

- Adaptive code work reads the catalog-generated quality contract and matching Obsidian broad `Model Switch.md` by project/task/module/file/symbol/code context. Score bands are `0-24` small, `25-49` standard, `50-74` complex, and `75-100` advanced. One Real PASS retains a quality pair, two PASS results downgrade one rung, and quality FAIL upgrades one rung.
- A low-risk, low-ambiguity text/code edit in the small band tries Spark first. A zero-result, zero-token Spark operational failure may immediately use the contextual quality pair. An Ending correctness/quality failure suppresses Spark for the matching project/task/operation/code-kind/score-band context and upgrades the next matching task to the quality pair. Spark remains available for fixed disjoint-source schedule branches.
- Old local `model_experience.json` remains legacy read-only. Every adaptive code profile retains `code-skill` ownership; Obsidian selects within the highest registered numeric GPT family and learns its verified boundary. Older numeric families remain catalog-only.
- An admitted fallback must already be allowed by Task Analyze and must carry its runtime reroute/receipt evidence. Inline execution does not invent fallback metadata.
- Image-dependent, broad integration, or evidence-heavy work uses a balanced/frontier cold start inside that highest family; verified bounded work descends only within the active family and its efforts.
- A planned label is not execution proof. Return receipt evidence only when an admitted route, explicit benchmark, or routing acceptance target requires it.

## Workflow

1. Confirm the request or admitted node names an active registered code domain and `code-skill`.
2. Read the relevant references and existing source.
3. Resolve important assumptions internally and choose the smallest viable design; ask only when a missing choice genuinely blocks safe implementation.
4. Preserve Qin's existing style, naming, structure, and unrelated user changes.
5. Keep Python signatures, calls, and literals on one line when the project/global rules require that style.
6. Implement only the requested behavior; avoid unrequested abstractions, features, fallbacks, or compatibility layers.
7. Run one bounded producer-side Quick Check. For light/local code, run the smallest safe smoke that exercises the changed function or direct path. For external-API, large-file, expensive-build, destructive, or side-effect-heavy work, do not execute the heavy path; check syntax plus the changed function, variable, import, and direct-reference names without importing code that may trigger side effects. This is a basic completion check, not independent Real Verify.
8. Present `CODE READY` with changed paths, concrete behavior, `Complexity: <score>/100 (<band>)`, `Route change: <direction and pair>`, and `Quick Check: PASS` or `Quick Check: SKIPPED (heavy) — <static evidence>`. Quick Check time is included in first-result latency.
9. Start the scored lifecycle ledger and bind the producer receipt when present. End Task is hard-required. For code that needs verification, build a real-test plan with `verify-skill/scripts/ending_verification_plan.py`; create one independently scored/modelled `End Task-{task}-{check}` per independent acceptance check. Each task runs its actual command. All checks must PASS. A FAIL creates a separate `Fix Task-{task}-{check}` with the exact error, followed by a fresh Ending check, for up to three repair attempts. When thread tools are unavailable, return terminal `BLOCKED` plus the exact handoffs; never treat the lifecycle as verified, emulate task creation, wait, poll, self-verify, or use a same-task Ending subagent.

The smallest safe syntax, existence, direct-reference, or focused local execution check belongs to producer Quick Check. Full builds, broad lint, integration/API calls, large-file processing, live side effects, and regressions belong to the detached Ending thread unless they are themselves the user's requested task.

The mandatory post-result Ending lifecycle still runs. Return published code after Quick Check, then release the real-test Ending tasks. The origin does not poll them. A failing Ending verifier records exact evidence and launches a separate repair task; the repaired code gets a fresh different verifier. The lifecycle always records score/band, check evidence, selected verifier pair, and repair chain locally; a receipt-backed producer terminal event also records score, route direction, and next pair in Obsidian.

## Optimization Boundary

When optimization is explicitly requested or admitted, implement only the authorized change and return raw before/after inputs, outputs, token/time evidence when relevant, and known risks. The optimization implementer never self-certifies same behavior. A different `verify-skill` worker performs independent verification after the result; an admitted route may schedule that worker in Ending Task.

When optimization is not the requested result, report a discovered candidate instead of silently expanding scope. An admitted route may place it in Ending Task; inline work does not create background work merely to record the idea.

## Generated File Placement

Put temporary code, fixtures, logs, receipts, and test outputs in the task/project `cache/` or `work/` area. Put final deliverables only in the requested location or active workspace `outputs/`.

## Guardrails

- Preserve execution order, side effects, exception behavior, Unity main-thread rules, and public contracts unless the request changes them.
- Do not parallelize order-sensitive or shared-state code without an authorized plan and independent comparison.
- Do not claim independent Real Verify before the different verifier completes.
- Do not push or publish unless explicitly authorized.

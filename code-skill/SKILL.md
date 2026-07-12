---
name: code-skill
description: "Do not use for an exact-scoped read-only lookup, audit, transform, or workflow reconstruction, even when sources are Python, C#, or Unity C#; the inline bootstrap handles it without skills. Use for code implementation, edit, execution, debug, refactor, authored tests/probes, or domain reasoning beyond that supplied scope, directly inline or as a positively admitted node."
---

# Code Skill

Use this as the global executor for active registry-owned code work that needs domain behavior or style rules. Ordinary implementation work enters directly from the hookless inline bootstrap on the current model. A self-contained bounded read-only lookup or audit with exact source/output scope stays on the bootstrap and does not load this skill. If Task Analyze has explicitly activated and positively admitted delegation, Workflow may instead deliver an exact locked code node. Inline execution needs no Workflow, child receipt, or model verifier; admitted execution must not reselect its pair or dependencies.

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
- Spark and fallback behavior: `references/spark-small-code.md`.

Active registry-owned code domains share this executor while retaining separate evidence keys and references. Current examples are `python`, `csharp`, and `unity_csharp`; `code_unspecified` is migration/history-only. Registry metadata identifies the domain; language rules are documented in this skill's `references` directory (for example, `python-rules.md`, `csharp-rules.md`, and `unity-csharp-rules.md`).

For prompt-in-code work, use `Prompt idea -> Prompt goal -> observed problems -> smallest complete solution` as an internal reasoning checklist, inspect the existing prompt and validators, and apply the complete `prompt-skill` contract plus only the conditional controls that materially improve behavior before the language-specific reference. Do not show a planning preamble; present the completed change before Ending Real verifies it.

## Model Contract

- Ordinary inline code work intentionally uses the current user-selected model and performs no foreground downgrade/upgrade or verification trial.
- For an explicit benchmark or admitted tiny code route, use Spark-low only for obvious bounded, low-risk, easy, low-ambiguity text-only tiny implementation, repair, refactor, command, or probe work. Its candidate route is exactly Spark-low plus the full normal fallback; Spark-medium/high/xhigh are never routing fallbacks.
- Every admitted non-tiny code profile retains `code-skill` ownership and the exact full Luna-low→Sol-ultra candidate ladder with no Spark. Coding can be easy or complex; task type never fixes the selected pair.
- An admitted fallback must already be allowed by Task Analyze and must carry its runtime reroute/receipt evidence. Inline execution does not invent fallback metadata.
- In an explicit benchmark or admitted route, image-dependent, over-context, broad integration, or evidence-heavy work may use planned Terra; bounded Spark-unavailable work may use planned Luna.
- A planned label is not execution proof. Return receipt evidence only when an admitted route, explicit benchmark, or routing acceptance target requires it.

## Workflow

1. Confirm the request or admitted node names an active registered code domain and `code-skill`.
2. Read the relevant references and existing source.
3. Resolve important assumptions internally and choose the smallest viable design; ask only when a missing choice genuinely blocks safe implementation.
4. Preserve Qin's existing style, naming, structure, and unrelated user changes.
5. Keep Python signatures, calls, and literals on one line when the project/global rules require that style.
6. Implement only the requested behavior; avoid unrequested abstractions, features, fallbacks, or compatibility layers.
7. Show the changed path and concrete behavior immediately; do not launch a child receipt or verifier before presentation.
8. After presentation, Ending Task runs proportional Real Verify such as syntax, compile, focused execution, or relevant regression. A failure notifies, reopens, repairs, and presents the correction.

Compile, import, lint, schema, build, existence, and focused execution checks belong to post-result Real Verify unless they are themselves the user's requested task.

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

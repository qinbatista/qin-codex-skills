---
name: code-skill
description: "Registry-owned code-domain executor selected in the locked task-analyze-skill plan and coordinated by workflow-skill. Built-in examples are Python, plain C#, and Unity C#. Tiny routes are Spark-low plus the full normal fallback; every non-tiny route uses the exact full normal ladder without Spark."
---

# Code Skill

Use this as the global executor for every active registry-owned code domain. `task-analyze-skill` chooses the code node's model, effort, dependencies, and stop condition; `workflow-skill` delivers that locked node. Do not reselect the route inside `code-skill`.

## Internal Route Selection

### Required Scope

Load this skill for every task node that reads, writes, explains, debugs, refactors, tests, or authors probes in an active registry-owned code domain, including:

- Python;
- C# or Unity C#;
- prompts embedded in Python/C# executable behavior;
- Python/C# helper scripts used by another skill;
- Python/C# optimization implementation.

Use only the locked registered domain; other production language domains remain with their owning production skill until explicitly registered here.

## Execution-domain routing

| Work | `execution_domain` | Rules |
|---|---|---|
| Python | `python` | `references/python-rules.md` |
| Plain non-Unity C# | `csharp` | `references/csharp-rules.md` |
| Unity C# | `unity_csharp` | `references/csharp-rules.md` then `references/unity-csharp-rules.md` |
| Legacy code with no domain | `code_unspecified` | migration/history-only; do not use for new work |

Any new active code domain is registry-owned by `routing_policy.py::EXECUTION_DOMAINS` and follows the [extension guide](../task-analyze-skill/references/router-extension-guide.md). Do not infer a new domain from a similar name.

## References

Read only what the locked node needs:

- all non-trivial code: `references/coding-approach.md`;
- Python: `references/python-rules.md`;
- plain C#: `references/csharp-rules.md`;
- Unity C#: `references/csharp-rules.md` and `references/unity-csharp-rules.md`;
- prompt-in-code: `references/prompt-generation.md`;
- safe repeated/parallel registered-code work: `references/parallelization.md`;
- Spark and fallback behavior: `references/spark-small-code.md`.

Active registry-owned code domains share this executor while retaining separate evidence keys and references. Current examples are `python`, `csharp`, and `unity_csharp`; `code_unspecified` is migration/history-only. Registry metadata identifies the domain; language rules are documented in this skill's `references` directory (for example, `python-rules.md`, `csharp-rules.md`, and `unity-csharp-rules.md`).

For prompt-in-code work, show `Prompt idea -> Prompt goal -> Problems -> Solution`, inspect the existing prompt, fix the smallest complete logic, then embed and Mini Verify it.

## Model Contract

- Use Spark-low only for obvious bounded, low-risk, easy, low-ambiguity text-only tiny implementation, repair, refactor, command, or probe work. Its candidate route is exactly Spark-low plus the full normal fallback; Spark-medium/high/xhigh are never routing fallbacks.
- For every non-tiny code task, retain `code-skill` ownership and the exact full Luna-low→Sol-ultra candidate ladder with no Spark. Coding can be easy or complex; task type never fixes the selected pair.
- Use only a fallback already allowed by Task Analyze, with a visible reason and runtime reroute/receipt when available.
- Never keep the entry model merely because it is active.
- Image-dependent, over-context, broad integration, or evidence-heavy work may use planned Terra; bounded Spark-unavailable work may use planned Luna.
- A planned label is not execution proof. Return receipt evidence when the workflow requires it.

## Workflow

1. Confirm the node names an active registered code domain and `code-skill`.
2. Read the relevant references and existing source.
3. State important assumptions and choose the smallest viable design.
4. Preserve Qin's existing style, naming, structure, and unrelated user changes.
5. Keep Python signatures, calls, and literals on one line when the project/global rules require that style.
6. Implement only the requested behavior; avoid unrequested abstractions, features, fallbacks, or compatibility layers.
7. Return the changed path, concrete behavior, and focused Mini Verify target to `workflow-skill`.
8. After Mini Verify passes, the main result may be shown. Real code-path testing, broader regressions, and independent optimization verification run in Ending Task.

Compile, import, lint, schema, build, or existence checks may satisfy the basic Mini Verify when proportional. They do not become Real Verify merely by being labeled tests.

## Optimization Boundary

When optimization is explicitly planned, implement only the authorized change and return raw before/after inputs, outputs, token/time evidence when relevant, and known risks. The optimization implementer never self-certifies same behavior. A different `verify-skill` worker performs Real Verify in Ending Task.

When optimization is not the requested result, report a discovered candidate to the parent instead of silently expanding scope. Task Analyze may place it in Ending Task.

## Generated File Placement

Put temporary code, fixtures, logs, receipts, and test outputs in the task/project `cache/` or `work/` area. Put final deliverables only in the requested location or active workspace `outputs/`.

## Guardrails

- Preserve execution order, side effects, exception behavior, Unity main-thread rules, and public contracts unless the request changes them.
- Do not parallelize order-sensitive or shared-state code without an authorized plan and independent comparison.
- Do not claim Real Verify before the Ending worker completes.
- Do not push or publish unless explicitly authorized.

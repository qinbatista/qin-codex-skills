---
name: code-skill
description: "Python/C# executor selected in the locked task-analyze-skill plan and coordinated by workflow-skill. Use for Python, C#, Unity C#, prompt-in-code, tests/probes, debugging, refactoring, explanation, or bounded optimization implementation. Spark is first for text-only Python/C# work. Preserve Qin's coding style, keep changes surgical, and return the code path to Mini Verify before the main result."
---

# Code Skill

Use this as the only global Python/C# executor. `task-analyze-skill` chooses the code node's model, effort, dependencies, and stop condition; `workflow-skill` delivers that locked node. Do not reselect the route inside `code-skill`.

## Internal Route Selection

### Required Scope

Load this skill for every task node that reads, writes, explains, debugs, refactors, tests, or authors probes for:

- Python;
- C# or Unity C#;
- prompts embedded in Python/C# executable behavior;
- Python/C# helper scripts used by another skill;
- Python/C# optimization implementation.

Do not use it for JavaScript, TypeScript, frontend, shell, SQL, config-only work, pure prose, images, account switching, or GitHub sync unless the planned node also touches Python/C#.

## References

Read only what the locked node needs:

- all non-trivial code: `references/coding-approach.md`;
- Python: `references/python-rules.md`;
- C#/Unity: `references/unity-csharp-rules.md`;
- prompt-in-code: `references/prompt-generation.md`;
- safe repeated/parallel Python/C# work: `references/parallelization.md`;
- Spark and fallback behavior: `references/spark-small-code.md`.

For prompt-in-code work, show `Prompt idea -> Prompt goal -> Problems -> Solution`, inspect the existing prompt, fix the smallest complete logic, then embed and Mini Verify it.

## Model Contract

- Use Spark first for text-only Python/C# implementation, bounded repair/refactor, and authored Python/C# probes at the effort in the locked plan.
- Use only a fallback already allowed by Task Analyze, with a visible reason and runtime reroute/receipt when available.
- Never keep the entry model merely because it is active.
- Image-dependent, over-context, broad integration, or evidence-heavy work may use planned Terra; bounded Spark-unavailable work may use planned Luna.
- A planned label is not execution proof. Return receipt evidence when the workflow requires it.

## Workflow

1. Confirm the node is Python/C# and the locked route names `code-skill`.
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

---
name: code-skill
description: "Use for code creation, repair, refactoring, and review when structure, ownership, or lifecycle decisions matter. Provides general coding philosophy and Python guidance. Exact read-only lookups and mechanical commands need no code-design workflow."
---

# Code Skill

Before any write, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Keep source and deliverables with their owners. Put all scratch in the owning project Cache from its first write, and check exact paths and the Git index before committing.

Give child processes explicit output paths and temporary environments. Tests, logs, caches and staging go directly to the execution's `temp-*` run, even for producers in `remote-*`. Synchronize only accepted, current data that the verified final owner consumes.

## Scope

Apply these writing and structure rules to every local code change in any language, including tests, scripts and temporary code. Follow the domain Skill for its APIs and implementation. Running an unchanged command or an exact read-only lookup skips the code-design workflow.

Briefly explain the intended result, acceptance criteria and implementation steps before detailed execution. Apply [Task Analyze's action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests) through failure recovery.

## Workflow

1. Run the [project AI-index startup gate](../management-skill/references/project-ai-index.md) before reading the current project. Reference projects skip the gate and maintenance. Honor applicable root and nested guidance. Follow [code navigation](../management-skill/references/project-ai-index.md#code-navigation) from module to file to exact method or anchor. Recall [project memory](../project-memory-skill/SKILL.md) with the same project/module/file/symbol selectors. Missing memory is a normal skip. Read the implementation and necessary caller, callee, state and test contracts. Consult broader architecture only for a concrete ownership or dependency question. Fresh source and current user instructions take precedence.
2. Read [code-writing philosophy](references/code-writing-philosophy.md) and only the applicable references below. Keep coherent operations with their owners, justify new methods and preserve unrelated work. Update touched stable AI-index routes and contracts after moves, renames, deletions or logic changes. Keep dated outcomes and evidence in project memory. Index stable entry points and contracts only.
3. Before adding a maintained Python test or starting extended testing, follow [Verify's testing Skill and test levels](../verify-skill/SKILL.md#project-testing-skill-and-test-levels). Verify changed code in this active task with a real readback or behavior check at the smallest relevant boundary. Fix failures before claiming completion.
4. Report changed behavior, evidence and remaining limitations. Ending's memory branch consolidates durable architecture, module and method contracts in the project store. It does not verify or repair code. The parallel [Workflow resource audit](../workflow-skill/references/ending-resource-audit.md) releases completed scratch and preserves active and user review/reuse resources.

## References

| Work | Read |
| --- | --- |
| Long source/text, build output or machine error logs | [Workflow's bounded text and log reading](../workflow-skill/references/text-and-log-reading.md) |
| Python | [Python rules](references/python-rules.md) |
| UI, PDF/report layout, or other visual presentation | [Coding approach and UI preferences](references/coding-approach.md) |
| Embedded prompts | [Prompt Skill](../prompt-skill/SKILL.md), then [prompt strings](references/prompt-generation.md) |
| Authorized parallel implementation | [Parallelization](references/parallelization.md) |
| Async results, pooled reuse, caches, configuration handoffs, or external retries | [State and side effects](references/state-and-side-effects.md) |
| Host helpers, scripts, subprocesses, or tests | [Portable, quiet execution](references/skill-platform-compatibility.md) |

For other languages, use the [installed Skill routing guide](../task-analyze-skill/references/global-skill-routing.md) to find their writing rules and source checkers.

## Verification

Use focused tests, direct-reference checks or a small real fixture. Use syntax checks and mocks for diagnosis and require runtime evidence for runtime claims. Inspect rendered UI at relevant desktop and narrow widths. For Python style, use `scripts/code_rule_guard.py --diff-from HEAD <changed-files>` on added lines alongside behavior checks.

Do not start the whole project or run a full build unless the user requests it. Avoid costly, destructive or external side effects for routine checks. Finish the authorized change and focused checks, then identify any behavior that still needs broader verification.

## Guardrails

Preserve public contracts, serialization, execution order, exceptions, cancellation and thread affinity unless the request changes them. Publish only when authorized.

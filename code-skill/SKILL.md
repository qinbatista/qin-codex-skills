---
name: code-skill
description: "Use for code creation, repair, refactoring, and code review when writing style, structure, or lifecycle decisions matter. Provides general preferences with Python and Unity C# references. Exact read-only lookups and mechanical commands need no code-design workflow."
---

# Code Skill

Before any file write, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Resolve task support in the owning project Cache from its first write, including child-tool caches and test output. Maintained source and final deliverables keep their actual owners; inspect exact paths and the Git index before committing.

## Scope

Apply this workflow to every local code change in any language, including tests, scripts and temporary code; another domain Skill may own its specific APIs and implementation. These are structure and writing preferences, not feature recipes. Running an unchanged command or an exact read-only lookup does not require the code-design workflow.

Briefly explain the intended change and implementation steps before detailed execution. Define the result and acceptance criteria from the user's request and relevant context. Carry out the change and handle failures under [Task Analyze's action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests).

## Workflow

1. Run the [project AI-index startup gate](../management-skill/references/project-ai-index.md) before reading the current task project, then follow its [code navigation](../management-skill/references/project-ai-index.md#code-navigation) from owning module to file and exact method or stable anchor. Honor root and applicable nested guidance. Consulting another project is reference work: skip its AI-index gate, prompts and maintenance under the shared scope rule. Recall [project memory](../project-memory-skill/SKILL.md) using those same project/module/file/symbol selectors; missing memory is a normal skip. Read the affected implementation and only the necessary caller, callee, state and test contracts to establish its logic chain. Consult broader architecture only when ownership or a concrete dependency requires it; fresh source and current user instructions take precedence.
2. Read [code-writing philosophy](references/code-writing-philosophy.md) and only the references needed below. Keep one coherent operation in its existing owner, justify any new method, and make the smallest complete change while preserving unrelated work. Update touched stable entry points, contracts and necessary links in the project AI index after a move, rename, deletion or logic-chain change; keep dated outcomes and source-bound verification in project memory, not the index. Do not index disposable code or copy implementations into guidance.
3. Before adding a maintained Python test file or starting extended project testing, follow [Verify's project testing Skill discovery and test levels](../verify-skill/SKILL.md#project-testing-skill-and-test-levels). Verify changed code in this active task using a real readback or behavior check at the smallest convincing boundary. Fix failures here before claiming completion.
4. Report the changed behavior, evidence, and remaining limitations. Ending's memory branch summarizes durable project knowledge and consolidates affected architecture, module and method contracts; it does not verify or repair code. Its parallel [Workflow resource audit](../workflow-skill/references/ending-resource-audit.md) releases completed disposable work while preserving active resources and user review/reuse. Avoid a separate memory file for each task or method.

## References

| Work | Read |
| --- | --- |
| Long source/text, build output or machine error logs | [Workflow's bounded text and log reading](../workflow-skill/references/text-and-log-reading.md) |
| Python | [Python rules](references/python-rules.md) |
| C# | [Unity C# common style](references/unity-csharp-rules.md); Unity-specific rules apply only to Unity |
| UI, PDF/report layout, or other visual presentation | [Coding approach and UI preferences](references/coding-approach.md) |
| Unity gameplay ownership or patterns | [Game structure](references/unity-game-code-structure-design.md) |
| Unity callbacks, async, serialization | [Lifecycle and serialization](references/unity-lifecycle-and-serialization.md) |
| Unity services or optional SDKs | [Service integration](references/unity-service-integration.md) |
| Embedded prompts | [Prompt Skill](../prompt-skill/SKILL.md), then [prompt strings](references/prompt-generation.md) |
| Authorized parallel implementation | [Parallelization](references/parallelization.md) |
| Async results, pooled reuse, caches, configuration handoffs, or external retries | [State and side effects](references/state-and-side-effects.md) |
| Host helpers, scripts, subprocesses, or tests | [Portable, quiet execution](references/skill-platform-compatibility.md) |

## Verification

Use focused function tests, direct-reference checks, or a small real fixture according to the changed behavior. Syntax validation and mocks can support diagnosis but do not prove runtime behavior. For rendered UI, inspect the affected state at relevant desktop and narrow widths; source/CSS alone does not prove alignment. For changed Python/C# style, `scripts/code_rule_guard.py --diff-from HEAD <changed-files>` checks newly added lines without rewriting legacy code. The guard supplements behavior evidence.

Do not start the whole project, run a full build, or compile all of Unity just to check a local change unless the user requests it. Complete the authorized change and available focused checks before reporting a limit that requires broader execution; separate implemented behavior from unverified claims. Do not execute expensive, destructive, or external side effects solely for a routine check.

## Guardrails

Preserve public contracts, serialization, execution order, exceptions, cancellation, and Unity main-thread rules unless the request changes them. Publish only when authorized. Put temporary support in the owner resolved by the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md).

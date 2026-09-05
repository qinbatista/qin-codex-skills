---
name: code-skill
description: "Use for code creation, repair, refactoring, and code review when writing style, structure, or lifecycle decisions matter. Provides general preferences with Python and Unity C# references. Exact read-only lookups and mechanical commands need no code-design workflow."
---

# Code Skill

## Scope

Apply general code preferences in any language; another domain Skill may own its specific APIs and implementation. These are structure and writing preferences, not feature recipes. A mechanical shell command or temporary execution script with no relevant design preference may remain skill-free.

Use the user's selected model and effort for work governed by these rules, including a delegated subtask. Do not downgrade that work by complexity score. The main model understands the request, selects relevant context, and defines each subtask's goal and acceptance criteria.

## Workflow

1. Read the nearest project `AGENTS.md`, the owning source, and relevant project memory on every task. Use [project memory](../project-memory-skill/SKILL.md) for scoped lookup; if no memory is available, continue. Never import another project's facts or turn a project-specific preference into a global rule. Fresh source and current user instructions take precedence over memory.
2. Read [code-writing philosophy](references/code-writing-philosophy.md) and only the references needed below. Identify the existing owner and make the smallest coherent change, preserving unrelated work.
3. Verify meaningful behavior in this active task using the smallest convincing check. Fix failures here before claiming completion. A simple value-only change may skip verification.
4. Report the changed behavior, evidence, and remaining limitations. Ending only summarizes durable project memory, using the user's selected model and effort; it does not verify or repair code.

## References

| Work | Read |
| --- | --- |
| Python | [Python rules](references/python-rules.md) |
| C# | [Unity C# common style](references/unity-csharp-rules.md); Unity-specific rules apply only to Unity |
| UI, PDF/report layout, or other visual presentation | [Coding approach and UI preferences](references/coding-approach.md) |
| Unity gameplay ownership or patterns | [Game structure](references/unity-game-code-structure-design.md) |
| Unity callbacks, async, serialization | [Lifecycle and serialization](references/unity-lifecycle-and-serialization.md) |
| Unity services or optional SDKs | [Service integration](references/unity-service-integration.md) |
| Embedded prompts | [Prompt Skill](../prompt-skill/SKILL.md), then [prompt strings](references/prompt-generation.md) |
| Authorized parallel implementation | [Parallelization](references/parallelization.md) |
| Host helpers, scripts, subprocesses, or tests | [Portable, quiet execution](references/skill-platform-compatibility.md) |

## Verification

Use focused function tests, direct-reference checks, a small real fixture, or targeted syntax validation according to the risk. For rendered UI, inspect the affected state at relevant desktop and narrow widths; source/CSS alone does not prove alignment. For changed Python/C# style, `scripts/code_rule_guard.py --diff-from HEAD <changed-files>` checks newly added lines without rewriting legacy code. The guard supplements behavior evidence.

Do not start the whole project, run a full build, or compile all of Unity just to check a local change unless the user requests it. If only broader execution could prove a claim, state that limit and deliver the evidence actually obtained. Do not execute expensive, destructive, or external side effects solely for a routine check.

## Guardrails

Preserve public contracts, serialization, execution order, exceptions, cancellation, and Unity main-thread rules unless the request changes them. Publish only when authorized. Put temporary project support artifacts under the project's [Cache policy](../workflow-skill/references/project-cache-artifact-policy.md).

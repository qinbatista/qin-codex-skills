---
name: code-skill
description: "Executor skill under workflow-skill for Python and C# Codex code work only. Use when workflow-skill routes a task into writing, editing, refactoring, debugging, reviewing, optimizing, or explaining Python or C# code; prompt generation and prompt-in-code work for Python or C#; Python modules, scripts, tests, and snippets; C# and Unity C# MonoBehaviours, ScriptableObjects, managers, and gameplay systems; performance and parallelization opportunities for independent Python or C# workloads; and obvious bounded Python/C# code tasks that may use Spark when an allowed model route exists. Do not use this skill to author JavaScript, TypeScript, frontend, shell, SQL, or other languages unless another active instruction explicitly routes that work elsewhere. Its internal routes are multi-select: use every route that applies to the task, not a one-of choice."
---

# Code Skill

Use this as the single merged Python/C# code executor selected by `workflow-skill`. It replaces the former code-related global skills and routes to all relevant Python and C# internal branches without loading every detail every time.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

Select every route required by the current Python or C# request and artifact. This is multi-select, not one-of. Do not read irrelevant references for every code task.

- General implementation, assumptions, smallest viable path, naming, branching, and surgical edits: read `references/coding-approach.md`.
- Prompt generation, prompt rewriting, prompt embedding, Python prompt assignments, or C# prompt constants: read `references/prompt-generation.md`.
- Python modules, scripts, tests, snippets, or Python prompt assignments: read `references/python-rules.md`.
- C# or Unity C# MonoBehaviours, ScriptableObjects, managers, gameplay systems, editor scripts, or Unity performance work: read `references/unity-csharp-rules.md`.
- Independent repeated work, batch processing, expensive loops, performance optimization, or any discovered safe parallelization opportunity in Python or C#: read `references/parallelization.md`.
- Obvious bounded low-risk Python/C# code tasks where an allowed model/delegation route exists: read `references/spark-small-code.md`.

When multiple routes apply, use them together and read only those relevant references. For example, Python prompt code needs prompt generation plus Python rules; Unity gameplay code needs coding approach plus C# rules.

## Trigger

Use this skill for Python and C# code writing, editing, refactoring, debugging, review, optimization, explanation, prompt-in-code work, Unity C#, and small bounded Python/C# code tasks. Do not use it for JavaScript, TypeScript, frontend implementation, shell, SQL, config-only edits, pure prose, pure image generation, pure account switching, or GitHub sync unless the task also includes Python or C# code or helper-script work.

## Workflow

1. Classify the task: prompt generation, Python, C#/Unity C#, parallelization/performance, Spark-eligible small Python/C# code, or a combination.
2. Read the relevant reference file(s) from `references/`.
3. For all non-trivial code work, state important assumptions, choose the smallest viable path, and define a verifiable success condition.
4. During implementation, review, refactor, or optimization, actively look for repeated work whose units are independent. If code changes are in scope and `references/parallelization.md` says the parallel path can preserve the same observable result, optimize it immediately instead of leaving it as a suggestion.
5. For prompt work, create or improve the prompt first, then embed the generated prompt into the corresponding Python or C# text/code.
6. Keep edits surgical and preserve unrelated user work.
7. After any code is written or changed, run the narrowest real usage check through `verify-skill` unless the user explicitly forbids verification.
8. For code-related reports, generated report artifacts must show `Input`, `Used`, `Output`, and `Why Pass` for every passing case. Simple code test results can stay in chat when the command, output, and pass reason are easy to read there.

## Guardrails

- Keep this as the single code skill. Do not load or depend on old code sub-skills.
- Keep this skill scoped to Python and C# authoring. Do not stretch it to JavaScript, TypeScript, frontend code, shell scripts, SQL, or other languages just because the task is code-like.
- Do not duplicate testing/reporting workflows here when `verify-skill` owns real evidence and report generation.
- Do not claim full success without saying what was or was not verified.
- Do not add unrequested features, abstractions, configurability, fallbacks, or compatibility layers.
- Do not parallelize order-sensitive, shared-state, main-thread-only, or side-effect-heavy code unless the same result can be proven with a real comparison test.
- Do not touch unrelated files or user changes.

## Examples

- "Write a Python parser" -> read coding approach and Python rules, implement the smallest path, then run a real parser input through `verify-skill`.
- "Speed up this Python batch processor" -> read Python rules plus parallelization rules, parallelize independent item work when safe, and compare sequential and parallel outputs.
- "Improve this prompt in Python code" -> read prompt generation and Python rules, then test with a concrete prompt input/output shape.
- "Fix this Unity enemy controller" -> read coding approach and C# rules, then verify with Unity compile/runtime evidence where practical.
- "Optimize this C# pathfinding preprocessing" -> read C# rules plus parallelization rules, keep Unity API access on the main thread when applicable, and parallelize only pure data work with equivalent output.
- "Small obvious Python/C# code cleanup" -> consider the Spark route only when an allowed delegation/model route exists, then still verify.

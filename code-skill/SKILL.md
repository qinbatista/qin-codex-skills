---
name: code-skill
description: "Executor skill under workflow-skill for code-related Codex work. Use when workflow-skill routes a task into writing, editing, refactoring, debugging, reviewing, optimizing, or explaining code; prompt generation and prompt-in-code work; Python modules, scripts, tests, and snippets; Unity C# MonoBehaviours, ScriptableObjects, managers, and gameplay systems; performance and parallelization opportunities for independent Python or Unity C# workloads; and obvious bounded code tasks that may use Spark when an allowed model route exists. Its internal routes are multi-select: use every route that applies to the task, not a one-of choice."
---

# Code Skill

Use this as the single merged code executor selected by `workflow-skill`. It replaces the former code-related global skills and routes to all relevant internal branches without loading every detail every time.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

Select every route required by the current request and artifact. This is multi-select, not one-of. Do not read irrelevant references for every code task.

- General implementation, assumptions, smallest viable path, naming, branching, and surgical edits: read `references/coding-approach.md`.
- Prompt generation, prompt rewriting, prompt embedding, or Python prompt assignments: read `references/prompt-generation.md`.
- Python modules, scripts, tests, snippets, or Python prompt assignments: read `references/python-rules.md`.
- Unity C# MonoBehaviours, ScriptableObjects, managers, gameplay systems, editor scripts, or Unity performance work: read `references/unity-csharp-rules.md`.
- Independent repeated work, batch processing, expensive loops, performance optimization, or any discovered safe parallelization opportunity in Python or Unity C#: read `references/parallelization.md`.
- Obvious bounded low-risk code tasks where an allowed model/delegation route exists: read `references/spark-small-code.md`.

When multiple routes apply, use them together and read only those relevant references. For example, Python prompt code needs prompt generation plus Python rules; Unity gameplay code needs coding approach plus Unity C# rules.

## Trigger

Use this skill for code writing, editing, refactoring, debugging, review, optimization, explanation, prompt-in-code work, Python, Unity C#, and small bounded code tasks. Do not use it for pure prose, pure image generation, pure account switching, or GitHub sync unless the task also includes code or helper-script work.

## Workflow

1. Classify the task: prompt generation, general code, Python, Unity C#, parallelization/performance, Spark-eligible small code, or a combination.
2. Read the relevant reference file(s) from `references/`.
3. For all non-trivial code work, state important assumptions, choose the smallest viable path, and define a verifiable success condition.
4. During implementation, review, refactor, or optimization, actively look for repeated work whose units are independent. If code changes are in scope and `references/parallelization.md` says the parallel path can preserve the same observable result, optimize it immediately instead of leaving it as a suggestion.
5. For prompt work, create or improve the prompt first, then embed the generated prompt into the corresponding text or code.
6. Keep edits surgical and preserve unrelated user work.
7. After any code is written or changed, run the narrowest real usage test through `test-skill` unless the user explicitly forbids testing.
8. For code-related reports, the PDF must show `Input`, `Used`, `Output`, and `Why Pass` for every passing case.

## Guardrails

- Keep this as the single code skill. Do not load or depend on old code sub-skills.
- Do not duplicate testing/reporting workflows here when `test-skill` is active.
- Do not claim full success without saying what was or was not verified.
- Do not add unrequested features, abstractions, configurability, fallbacks, or compatibility layers.
- Do not parallelize order-sensitive, shared-state, main-thread-only, or side-effect-heavy code unless the same result can be proven with a real comparison test.
- Do not touch unrelated files or user changes.

## Examples

- "Write a Python parser" -> read coding approach and Python rules, implement the smallest path, then run a real parser input through `test-skill`.
- "Speed up this Python batch processor" -> read Python rules plus parallelization rules, parallelize independent item work when safe, and compare sequential and parallel outputs.
- "Improve this prompt in code" -> read prompt generation and any relevant language rules, then test with a concrete prompt input/output shape.
- "Fix this Unity enemy controller" -> read coding approach and Unity C# rules, then verify with Unity compile/runtime evidence where practical.
- "Optimize this Unity C# pathfinding preprocessing" -> read Unity C# rules plus parallelization rules, keep Unity API access on the main thread, and parallelize only pure data work with equivalent output.
- "Small obvious code cleanup" -> consider the Spark route only when an allowed delegation/model route exists, then still verify.

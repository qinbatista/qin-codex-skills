---
name: code-skill
description: Unified Qin code skill for all code-related Codex work. Use for writing, editing, refactoring, debugging, reviewing, optimizing, or explaining code; prompt generation and prompt-in-code work; Python modules, scripts, tests, and snippets; Unity C# MonoBehaviours, ScriptableObjects, managers, and gameplay systems; and obvious bounded code tasks that may use Spark when an allowed model route exists.
---

# Code Skill

Use this as the single merged code skill. It contains the former code-related rules in one place and should not depend on separate code sub-skills.

## Merged From

This one skill replaces the old code-related global skills:

- `qin-easy-code-spark` -> [Spark For Small Code Tasks](#spark-for-small-code-tasks)
- `qin-karpathy-guidelines` -> [Coding Approach](#coding-approach)
- `qin-prompt-creating` -> [Prompt Generation](#prompt-generation)
- `qin-python-code-checker` and its Python style reference -> [Python Rules](#python-rules)
- `qin-unity-csharp-minimal-style` -> [Unity C# Rules](#unity-c-rules)

## Workflow

1. Classify the task: prompt generation, general code, Python, Unity C#, small bounded task, or a combination.
2. For obvious bounded code tasks, decide whether Spark is appropriate before implementation.
3. For all non-trivial code work, state important assumptions, choose the smallest viable path, and define a verifiable success condition.
4. For prompt work, create or improve the prompt first, then embed the generated prompt into the corresponding text or code.
5. For Python or Unity C#, apply the language-specific rules in this skill.
6. Keep edits surgical, preserve unrelated user work, and verify with the narrowest practical check unless the user explicitly tells you not to test.

## Spark For Small Code Tasks

Use `GPT-5.3-Codex-Spark` for obvious, bounded, low-risk coding work when an allowed model-selection or delegation route exists.

Use Spark when all are true:

- The request is clearly bounded and affects one or a few files.
- The expected edit, cleanup, review target, or verification path is obvious from the request or shallow inspection.
- The task does not require deep debugging, architecture changes, security-sensitive reasoning, migrations, or broad repository archaeology.
- Verification is simple, such as a focused lint, test, build, type check, or direct file inspection.

Model names:

```text
GPT-5.3-Codex-Spark
gpt-5.3-codex-spark
```

If no allowed Spark route exists in the current environment, continue with the current model and mention that limitation only when it matters. Spark never bypasses project rules, language rules, or final review.

## Coding Approach

Think before coding:

- State assumptions explicitly when they matter.
- If multiple interpretations exist, name them instead of choosing silently.
- If the smallest correct fix turns into a large structural or architectural change, stop and ask with a short plan.
- Define what success looks like before implementing.

Prefer the simplest viable solution:

- Write the minimum code that solves the actual request.
- Do not add unrequested features, abstractions, configurability, fallbacks, compatibility layers, or defensive branches.
- Trust declared inputs, outputs, formats, and contracts. Fix the producer or contract instead of adding consumer-side repair logic.
- For exactly two mutually exclusive outcomes, use a plain `if`/`else`.
- For three or more outcomes, use the language's switch-style construct: Python `match`/`case`, C# `switch`/`case`, switch expressions, or guarded switch cases.

Keep edits surgical:

- Touch only what the request requires.
- Match local style unless this skill or a tighter repo instruction says otherwise.
- Remove only unused imports, variables, or helpers made obsolete by your own change.
- Identify the authoritative source path before editing, copying, moving, or generating files.
- Do not mix sibling packages, caches, clones, or workspaces just because filenames look similar.

Naming:

- Use correct English spelling for new identifiers, file names, keys, comments, and prompt labels.
- Keep an existing misspelled name only when required by an external API, persisted schema, third-party contract, or compatibility boundary.
- Use clear full-word names instead of unexplained abbreviations.

## Prompt Generation

Use this section only for AI prompt creation, rewriting, improvement, review, standardization, or prompt embedding. Do not use it for ordinary code style, architecture, debugging, or non-prompt prose.

Create compact Python prompt assignments ready to paste into code:

```python
prompt = f"""
...
"""
```

Prompt workflow:

1. Identify purpose, input variables, target audience, and desired output shape.
2. Choose a function prompt for direct AI operations such as get, extract, change, check, fix, convert, compare, or return structured output.
3. Choose a content prompt for text humans will read, such as descriptions, summaries, explanations, factory notes, doctor-facing notes, customer copy, or reviewer notes.
4. Use `Purpose:` followed by `Rules:`.
5. Keep the prompt concise. Merge overlapping rules instead of appending repeated warnings.
6. Treat examples, bad outputs, and edge cases as test evidence. Do not paste them into the prompt unless the example is the reusable requirement.
7. For Python f-strings, escape literal JSON braces as `{{` and `}}`; real interpolation placeholders stay single-braced, such as `{image_width}`.

Function prompt shape:

```python
prompt = f"""
Purpose:
Extract <target> from <source>.

Rules:
- <rule 1>
- <rule 2>

Output JSON format must be:
{{
  "<key>": "<value>"
}}
"""
```

Human-reading content prompt shape:

```python
prompt = f"""
Purpose:
Work from the perspective of <role> writing <content type> from <source/input> for <audience/use case>, emphasizing <most important qualities> first.

Rules:
- <rule 1>
- <rule 2>

Return JSON Format:
{{
  "<key>": "<value>"
}}
"""
```

Prompt guardrails:

- Do not start function prompts with persona text such as `You are...`.
- Let the output schema define the container shape and fields instead of repeating verbose JSON warnings.
- Do not add sibling-case warnings for cases the user did not mention.
- Do not add vague filler such as "be accurate" when a concrete rule can say what accuracy requires.
- Return only the optimized `prompt = f"""..."""` when the user asks for prompt code only.

## Python Rules

Apply these rules whenever writing or editing Python modules, classes, functions, scripts, tests, snippets, or Python prompt assignments.

Behavior:

- Preserve behavior unless the user explicitly asks for new behavior.
- For vague requests such as optimize, clean up, refactor, or improve, treat the task as style enforcement plus behavior-preserving micro-optimization only.
- Return only code when the user asks for raw Python output.

Formatting and structure:

- Keep function signatures and function or method calls on one line when reasonably possible.
- Preserve the existing manual formatting style of the touched file.
- Do not run `ruff format`, `black`, or any auto-formatter unless explicitly requested.
- Keep imports at the top of the file.
- Do not add demos, TODOs, unused imports, placeholder logic, or unnecessary `__main__` guards unless requested.

Names and variables:

- Use descriptive full-word names and correct English spelling.
- Avoid vague placeholder names such as `out`, `result`, `data`, `item`, `obj`, or `response` when a more specific meaning is known.
- Inline any value or variable used exactly once when it remains readable.
- Create variables only when reused or when they clearly improve readability.

Helpers and abstractions:

- Do not add one-off class helper methods that are only called by one other method.
- Do not add trivial module-level helper functions for short path joins, tiny normalization steps, or one-line predicates used by one local flow.
- Inline one-off logic into the actual method or function unless extraction removes real complexity or is reused.
- Do not keep awkward source logic in place and add wrappers, retry-only branches, or compatibility layers when the underlying function can be fixed directly.

Contracts and guards:

- Trust declared function inputs and return shapes.
- Do not repeatedly check `dict`, `list`, `int`, or similar types across call sites unless explicitly requested.
- Do not add fallback/default/compatibility branches, alternate input aliases, empty-value substitutes, or caller-side repair logic unless requested or required by a real external API contract.
- Do not validate or repair a called function's return format at the caller; fix the producing function, helper contract, or prompt instead.
- If an AI helper guarantees parsed JSON through `json_root="object"` or `json_root="array"`, use the returned `dict` or `list` directly with no `json.loads`, `ast.literal_eval`, string fallback, or duplicate parse check.
- For AI extraction, naming, or review flows, put semantic rules in the prompt and keep local code limited to minimal schema normalization.

Error handling:

- Use at most one `try`/`except` per function.
- Keep `try`/`except` scopes narrow when only one call is risky.
- When an `except` branch only logs and returns or raises, keep the log call on one physical line and inline single-use error formatting.

Branching:

- Use plain `if`/`else` for exactly two mutually exclusive outcomes.
- Use Python `match`/`case` for three or more outcomes.
- For complex predicates that are not one selector, use `match True` with guarded `case _ if ...` branches.
- Normalize string comparisons with `str(...).strip().lower()` before comparing; do not enumerate casing variants.

Logging:

Use exactly this call shape on one line when logging is part of the code:

```python
self.__log_manager.print(function_emoji, status_text, execute_time, function_name, log_message)
```

- `status_text` must be `"done"`, `"warning"`, `"error"`, or `"pass"`.
- Log exactly one success message per function at the end of the main successful path.
- Log only important failures or warnings, at most one log per failure branch.
- Do not log every branch or small step.

## Unity C# Rules

Apply these rules for Unity projects and C# code, including MonoBehaviours, ScriptableObjects, managers, gameplay systems, runtime scripts, reviews, explanations, refactors, and performance work.

Workflow:

1. Read repo-level `AGENTS.md`, local style notes, or direct user instructions, and let tighter local rules override this shared style.
2. Preserve core behavior unless the user explicitly asks for a functional change.
3. For optimize, simplify, or cleanup requests, keep edits inside the requested code path unless the user explicitly asks to broaden scope.

Output:

- Return the final updated C# code first when the user asks for code.
- Then briefly explain what changed and why in 1-3 short sentences unless the user asks for code only.

Unity structure:

- Use `Awake()` for data and component initialization owned by the script, such as `Rigidbody`, `Collider`, `Animator`, and internal fields.
- Use `Start()` for work that depends on other scripts, ScriptableObjects, services, or external references.
- Do not allocate new objects every frame in `Update()` if they can be reused.
- Store reusable objects in fields and initialize them once, usually in `Awake()`.

C# style:

- For a single statement, keep the entire `if` on one line without braces.
- Use braces only when the block contains more than one statement.
- Use plain `if`/`else` for exactly two mutually exclusive outcomes.
- Use `switch`/`case`, a switch expression, or guarded switch cases for three or more outcomes.
- Do not write or keep `if`/`else if` chains for three or more outcomes when C# can express the same behavior with `switch`.
- Inline a value when it is used exactly once and remains readable.
- Do not create helper functions that are only used once, except `Update()` may call one helper used only there when it makes the per-frame flow clearer.
- Do not create a new C# script only to simplify a very small or easy structure.
- Keep function calls and log calls on one line.
- Keep spaces after commas.
- Do not fold argument lists across multiple lines unless explicitly requested.

Fields and names:

- Default fields to `private`.
- Use underscore names for internal fields and internal locals, such as `_name`, `_currentY`, `_index`, `_offset`, `_damageValue`, `_randomSeed`, and `_enemyHealth`.
- Use clear full-word names instead of abbreviations like `dmg`, `rs`, or `hp`.
- Do not declare public fields by default.
- If something must be exposed, prefer a property with `get; set;`.
- If a field or value is initialized in `Awake()` or `Start()`, use it directly instead of adding repeated guards like `!= null` or `> 0`.

Unity guardrails:

- Do not add abstractions, wrappers, lifecycle changes, data-flow changes, or defensive checks for impossible states unless requested.
- Do not change multiple authoring, manager, or system scripts when the user asked only for local optimization; report the broader issue or ask before expanding scope.
- Do not let broader generic C# formatting advice override this style.

## Final Guardrails

- Keep this skill as the single code skill. Do not load or depend on old code sub-skills.
- Do not duplicate testing/reporting workflows here when a separate testing skill is active.
- Do not claim full success without saying what was or was not verified.

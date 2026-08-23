# Python Rules

Use `execution_domain=python` in routing evidence for Python work. This domain shares `code-skill` with other registry-owned code domains but is not interchangeable with their language rules or evidence.

Apply these rules whenever writing or editing Python modules, classes, functions, scripts, tests, snippets, or Python prompt assignments.

## Behavior

- Preserve behavior unless the user explicitly asks for new behavior.
- For vague requests such as optimize, clean up, refactor, or improve, treat the task as style enforcement plus behavior-preserving micro-optimization only.
- When independent repeated work is present or discovered during optimization, also read `references/parallelization.md` and parallelize only when the same observable result can be verified.
- Return only code when the user asks for raw Python output.

## Formatting And Structure

- Keep every function signature and every function/method call with parameters on one physical line, no matter how many parameters it has.
- Do not wrap argument lists over multiple lines. This includes constructors, builtins such as `any()`/`all()`, logging calls, helper calls, and chained method calls.
- Keep every Python dict, list, set, tuple, and comprehension literal on one physical line when it appears in executable code. This includes assignments such as `prompt_json = {...}`, return values, log payloads, and inline input/output objects.
- Do not write vertical payload literals like `prompt_json = { ... }`. Create clear intermediate variables first when needed, then keep the final literal on one line.
- For long calls, create clear intermediate variables first, then keep the final call on one line.
- Preserve the existing manual formatting style of the touched file.
- Do not run `ruff format`, `black`, or any auto-formatter unless explicitly requested.
- Keep imports at the top of the file.
- Do not add demos, TODOs, unused imports, placeholder logic, or unnecessary `__main__` guards unless requested.

## Names And Variables

- Use descriptive full-word names and correct English spelling.
- Avoid vague placeholder names such as `out`, `result`, `data`, `item`, `obj`, or `response` when a more specific meaning is known.
- Do not bind a value to `_`, and do not use `_` in tuple unpacking to suppress an unused return member. Access the required member directly, change the producer contract when it is owned here, or use a meaningful name only when the value is genuinely read. Pattern wildcards such as `case _` remain valid because they do not create a discarded value binding.
- Inline any value or variable used exactly once when it remains readable.
- Create variables only when reused or when they clearly improve readability.

## Helpers And Abstractions

- Do not add one-off class helper methods that are only called by one other method.
- Do not add trivial module-level helper functions for short path joins, tiny normalization steps, or one-line predicates used by one local flow.
- Inline one-off logic into the actual method or function unless extraction removes real complexity or is reused.
- Do not keep awkward source logic in place and add wrappers, retry-only branches, or compatibility layers when the underlying function can be fixed directly.
- Write logic functions step by step inside the owning function. When the input and return contract are confirmed, express any needed conditions in that function instead of adding wrapper functions, nested functions, or caller-side routing layers.
- Do not create a same-arguments, same-return pass-through function. Call the owning function once at the real call site unless the boundary adds validation, translation, transaction, lifecycle, platform, provider, or public compatibility semantics.
- Reject accidental self-recursion: a function must not call itself as its only action. Intentional recursion requires a visible base case and progress toward it.

## Contracts And Guards

- Trust declared function inputs and return shapes.
- When a source JSON key, object field, or return value is confirmed, read that exact value directly. Do not search sibling aliases, typo variants, protective keys, or backup holder objects such as `user_text`, `user`, `text`, and misspelled variants unless the real source contract requires them.
- Do not repeatedly check `dict`, `list`, `int`, or similar types across call sites unless explicitly requested.
- Do not add fallback/default/compatibility branches, alternate input aliases, empty-value substitutes, or caller-side repair logic unless requested or required by a real external API contract.
- Do not validate or repair a called function's return format at the caller; fix the producing function, helper contract, or prompt instead.
- If an AI helper guarantees parsed JSON through `json_root="object"` or `json_root="array"`, use the returned `dict` or `list` directly with no `json.loads`, `ast.literal_eval`, string fallback, or duplicate parse check.
- For AI extraction, naming, or review flows, put semantic rules in the prompt and keep local code limited to minimal schema normalization.

## Quick Check And Detached Ending

- Before presenting a light/local Python edit, run the smallest safe focused smoke that exercises the changed function. For API, large-file, expensive, destructive, or import-side-effect-heavy work, skip the heavy run; use `py_compile` or AST parsing plus direct changed function, variable, import, and reference checks.
- Before final Ending or release-gate PASS, run `code-skill/scripts/code_rule_guard.py --diff-from HEAD` on changed Python files so new discard bindings, pass-through wrappers, only-action self-recursion, and avoidable vertical calls fail deterministically without rewriting unchanged legacy code.
- Present `CODE READY` immediately after exactly one Quick Check. A durable Python change normally exposes `real_test` through that Quick Check and emits `ending-required`; any result with no `real_test`, `information_update`, or `memory_update` surface records `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_update`. When required, create and acknowledge one persistent global projectless Ending, then return without polling it. Use exact `create_thread` target `{"type":"projectless"}` and require `list_threads` readback with `projectId=null` or absent; project/current-task/subtask placement is BLOCKED. Its fixed Spark-xhigh controller runs direct checks and may use capability-routed Terra/Sol `ENDING_CHECK_WORKER` nodes for semantic runtime, code-quality, prompt, UI, or visual evidence. Multiple checks stay inside that one Ending lifecycle and every required check must PASS.
- Before durable result-memory closeout, compare the active Skill/AGENTS process contract, fresh real execution evidence, and effective project-result memory. Only a memory-only defect permits an append-only correction or projection reconciliation inside Ending. Skill or execution defects write no result memory and return exact evidence to the immutable origin session for repair and a fresh Ending. The next task reads only effective project-result memory and hides superseded records from active guidance.
- A failing verifier records the exact command/output/error and acceptance gap, then submits the generated repair prompt through `codex_app__send_message_to_thread` to the immutable origin session. That source session repairs only the authorized result, runs Quick Check, presents a new result, and starts a fresh Ending that reruns the original check with `--repair-of-lifecycle-id`; continue for at most three attempts. Missing source-session metadata or failed prompt submission is BLOCKED, and BLOCKED is not verified.
- Record an optional simplification idea without editing only when the delivered behavior is already correct and no repair is required.

## Error Handling

- Use at most one `try`/`except` per function.
- Keep `try`/`except` scopes narrow when only one call is risky.
- When an `except` branch only logs and returns or raises, keep the log call on one physical line and inline single-use error formatting.

## Branching

- Use plain `if`/`else` for exactly two mutually exclusive outcomes.
- Use Python `match`/`case` for three or more outcomes only when the runtime supports Python 3.10 or newer; use `if`/`elif` when a script must run on Python 3.9.
- For complex predicates that are not one selector, use `match True` with guarded `case _ if ...` branches only when Python 3.10+ is guaranteed.
- Normalize string comparisons with `str(...).strip().lower()` before comparing; do not enumerate casing variants.

## Logging

Use exactly this call shape on one line when logging is part of the code:

```python
self.__log_manager.print(function_emoji, status_text, execute_time, function_name, log_message)
```

- `status_text` must be `"done"`, `"warning"`, `"error"`, or `"pass"`.
- Log exactly one success message per function at the end of the main successful path.
- Log only important failures or warnings, at most one log per failure branch.
- Do not log every branch or small step.

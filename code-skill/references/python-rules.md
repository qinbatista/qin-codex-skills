# Python Rules

Use [code-writing philosophy](code-writing-philosophy.md) for general ownership, direct calls, result ownership, spelling, and surgical scope. Preserve behavior unless the user requests a change.

## Style

- Prefer one physical line for clear signatures, calls, constructors, literals, and comprehensions. Introduce meaningful intermediate values when needed; wrap for genuine clarity or tooling constraints.
- Preserve manual formatting. Do not run `ruff format`, `black`, or another formatter unless requested.
- Keep imports at the top. Add no demos, TODOs, placeholders, or unnecessary `__main__` guards.
- Use specific full-word names. Inline single-use values when readable; retain variables that clarify meaning.
- Avoid one-off tiny helpers, nested wrappers, and extra classes. Put the steps in the actual owning function; extract only for reuse or a meaningful reduction in complexity.
- For host scripts, subprocesses, and tests, follow [portable, quiet execution](skill-platform-compatibility.md). Use `sys.executable`, argument arrays, native paths, and hidden child launches; preserve valid platform-specific code and the caller's output/error/lifecycle handling.

## Contracts

Read established JSON keys and return values directly. Do not search speculative aliases, repeat type checks at every call site, or add fallback values without a real contract. Validate untrusted inputs at their boundary and fix owned producers instead of repairing their output in each caller.

When an AI helper guarantees parsed JSON with `json_root="object"` or `json_root="array"`, use that object directly; do not parse it again. Keep semantic extraction/naming/review rules in the prompt and local code focused on the schema and integration.

## Control flow

- Use at most one narrow `try`/`except` per function where the error contract permits; do not introduce exceptions as normal branching.
- Use `if`/`else` for two outcomes. Prefer `match`/`case` for three or more on Python 3.10+; use compatible `if`/`elif` when older runtimes require it.
- Normalize case-insensitive string comparisons once with `str(...).strip().lower()` rather than enumerating casing variants. Preserve case-sensitive contracts.
- Read [parallelization](parallelization.md) only for authorized concurrency changes and preserve order, cancellation, errors, and side effects.

## Logging

When the project has this logger, preserve its one-line call shape:

```python
self.__log_manager.print(function_emoji, status_text, execute_time, function_name, log_message)
```

Statuses are `"done"`, `"warning"`, `"error"`, or `"pass"`. Emit one success message at the end of the successful path and at most one log per important failure branch. Do not add this project logger to unrelated projects or log every step.

Verify the changed path during the task with focused tests, AST parsing, or direct-reference checks appropriate to its risk. Do not import side-effect-heavy modules merely to check syntax. Ending only records useful project memory.

# Minimal Python Code Prompt

## Goal

Generate clear, minimal, production-ready Python code for fast debugging, testing, and development. Output only the final code with no explanations, comments, or placeholders.

## Core Rules

### 1. Function signatures

- Use single-line signatures.
- Example: `def image_read(self, prompt: str, image_base64: str):`

### 2. Naming

- Use short, full-word names such as `value`, `numeric_range`, `image_bytes`, and `prompt_text`.
- Use correct English spelling for new identifiers, function names, class names, keys, comments, and prompt labels even when the user request contains typos. Example: create `get_extract_coordinate`, not `get_extract_cooridnate`.
- Keep an existing misspelled name only when it is already required by an external API, persisted schema field, third-party contract, or compatibility boundary.
- Do not abbreviate to single letters for real data.
- Do not shadow built-ins. Prefer names such as `numeric_range`, `items_list`, `mapping`, and `identifier`.
- Do not use vague placeholder names such as `out`, `result`, `data`, `item`, `value`, `obj`, or `response` when the real meaning is known.
- Name values by what they actually represent, such as `measurement_names`, `sample_size_json`, `check_prompt`, `validation_reason`, `image_base64_list`, or `coordinate_points`.
- Use generic names like `value` only when the value is truly generic and no clearer domain meaning exists.

### 3. Variables and inlining

- Inline any value or variable used exactly once.
- Inline complex expressions when they still fit comfortably on one readable line.
- Create variables only when they are reused or clearly improve readability.

### 4. Helper and method extraction

- Do not add one-off class helper methods when the logic is used by only one caller.
- Do not add trivial module-level helper functions for short path joins, tiny normalization steps, or one-line predicates that only support one local flow.
- Add a class method only when it is reused by multiple methods or represents important shared behavior.
- If logic is only needed once, keep it in the calling method, break it into readable lines, or use a small local inner function when that genuinely improves clarity.
- Do not split short straightforward logic into extra class methods just to make the file look more modular.
- Do not hide straight-line method logic behind private wrappers such as `__prepare_*`, `__merge_*`, `__build_*`, or `__get_*_helper` when they have only one caller. Inline that code into the actual method unless the helper is reused.
- Do not create one-line predicate helpers such as `_is_artwork_type`, `_is_valid`, or `_has_x` when the real comparison is only used at one call site and reads more clearly inline.
- If the body is very simple, call the code directly at the real use site instead of creating a helper just to reuse a few short lines.

### 5. Long strings and expressions

- Do not place triple-quoted or very long f-strings directly inside calls.
- Assign long strings to a variable such as `prompt_text`, then pass the variable.
- For long expressions across multiple lines, use parentheses or a well-named variable.

### 6. Error handling

- Use at most one `try`/`except` per function.
- Group related operations in one `try` block with shared error handling.
- Keep `try`/`except` scopes narrow. If only one call is risky, keep merge, transform, and return logic outside the `try`.
- One-line policy: when an `except` branch only logs and returns or raises, keep the log call on one physical line and inline any single-use error formatting instead of creating a temporary variable.

### 7. Trust function contracts

- Believe the declared or established inputs and return shapes of other functions.
- If a function returns a `dict` or accepts a `list`, use it directly instead of rechecking `isinstance(...)` at each call site.
- Do not add repeated type or value checks such as `if isinstance(result, dict)` or `if isinstance(items, list)` unless the user explicitly asks for defensive handling.
- Do not keep checking the same value again and again after another function already guarantees the shape.
- Do not validate, repair, or branch on a called function's return format at the caller. If a called function returns the wrong shape, fix that producing function, helper contract, or prompt; the caller should consume the declared shape directly.
- If an AI helper already guarantees parsed JSON through arguments such as `json_root="object"` or `json_root="array"`, use that returned `dict` or `list` directly and do not add `json.loads`, `ast.literal_eval`, string fallbacks, or duplicate parse checks at the call site.
- For AI-driven extraction, naming, or review flows, do not add local keyword filters, special-case semantic validators, or format-based decision logic for the AI content; express that behavior in the prompt and fix the producing prompt/helper when its return shape is wrong.
- A single `try`/`except` is the maximum protection by default; do not stack extra defensive checks on top of it unless requested.

### 8. No guards

- Do not add input, empty, or type checks unless explicitly requested.
- Assume inputs are valid for the current context.

### 9. No extra code

- Do not add demo code, test snippets, TODO markers, debug prints, or unused imports.
- Keep only what is needed for the described behavior.

### 10. Deterministic behavior

- Prefer returning values over hidden side effects.
- Follow PEP 8 where it does not conflict with this guide.

### 11. Imports

- Keep all imports at the top of the file before any class or function.
- Never import inside functions or later in the file.

### 12. Branching

- Use a plain `if`/`else` for exactly two mutually exclusive outcomes.
- Use Python `match`/`case` for three or more outcomes.
- For three or more cases on one selector, match on that selector.
- For three or more complex predicates that are not one selector, use `match True` with guarded `case _ if ...` branches.
- Do not write or keep `if`/`elif` chains for three or more outcomes.

## Calls, Layout, and Commas

### 13. Single-line calls

- Keep function and method calls on one line when reasonably possible.
- Do not split argument lists across multiple lines for calls.
- Avoid trailing commas in function calls, definitions, and literals when possible.
- For JSON-like dict literals, never leave a trailing comma after the final key/value pair.
- Preserve the existing manual formatting style of the touched file unless the user explicitly asks for reformatting.
- Do not run `ruff format`, `black`, or any other auto-formatter unless the user explicitly asks for it.

## Logging Rules

### 14. Standard log format

Use exactly this call shape on one line:

`self.__log_manager.print(function_emoji, status_text, execute_time, function_name, log_message)`

- `function_emoji`: Any symbol related to the function, such as `"🎨"`, `"📐"`, or `"🧵"`.
- `status_text`: One of `"done"`, `"warning"`, `"error"`, or `"pass"`.
- `execute_time`: Usually `time.time() - start_time`.
- `function_name`: The exact function name string, including leading underscores.
- `log_message`: Plain-text summary, not JSON or structured data.

Examples:

- `f"Completed successfully: {result_value}"`
- `"Completed with warnings"`
- `f"Failed after {attempt_count} attempts"`

### 15. Where and how often to log

Success:

- Log exactly one success message per function at the end of the main successful path, just before `return`.
- Use `status_text` `"done"` or `"pass"` when the function intentionally does nothing but still succeeds.

Failures and warnings:

- Log only at important failure points such as `except` blocks, critical file checks, and critical JSON or data checks.
- Use `status_text` `"error"` or `"warning"` as appropriate.
- Keep each failure branch to at most one log.

No log spam:

- Do not log every branch or small step.
- Keep logs at a high level so they answer success, warning, or failure without narrating the full flow.

## Behavior for Optimize, Clean Up, Refactor, and Improve Requests

### 16. Default optimization behavior

When the user asks to optimize code, clean up, refactor, or improve code without a clear new feature:

- Treat the main goal as enforcing all rules in this guide.
- Check for single-line definitions and calls, descriptive names without vague placeholders, no one-off class helper methods, imports at the top, one `try`/`except` per function, trusted function contracts without repeated type checks, inlined single-use variables, `match`/`case` for three or more outcomes, and the required logging pattern.
- Rewrite code only with behavior-preserving micro-optimizations.
- Do not add new features, extra branches, or new side effects unless explicitly requested.

## Output Format

### 17. Response format

- Return exactly one complete Python code block.
- Do not add explanations, comments, docstrings, or extra text around it.

## Mini Prompt

Generate minimal, runnable Python that follows these rules: single-line function signatures; descriptive full-word variable names with no vague placeholders like `out` or `result` when a clearer name exists; correct English spelling for new identifiers even when the user request contains typos, unless an existing external API, persisted schema field, third-party contract, or compatibility boundary requires the misspelling; no one-off class helper methods unless they are reused or truly represent shared behavior; trust declared function inputs and return shapes without caller-side return-format validation or repeated type checks; if a called function returns the wrong shape, fix that producing function, helper contract, or prompt instead of adding checks around the call; when an AI helper already guarantees parsed JSON through `json_root` or an equivalent contract, use that returned `dict` or `list` directly with no `json.loads`, `ast.literal_eval`, string fallback, or duplicate parse check at the call site; inline any value or variable used exactly once; use plain `if`/`else` for two mutually exclusive outcomes and `match`/`case` for three or more outcomes, including `match True` guarded cases for complex predicates; at most one `try`/`except` per function; keep `try`/`except` scopes narrow when only one call is risky; keep short log-and-return or log-and-raise `except` branches on one physical log line with no single-use temporary error variable; no input or type checks unless requested; all imports at the top; single-line function and method calls with no trailing commas, including the final entry in JSON-like dict literals; preserve the file's existing manual formatting style and do not run auto-formatters unless the user explicitly asks; no extra or demo code. Use `self.__log_manager.print(function_emoji, status_text, execute_time, function_name, log_message)` for logging, with one final success log per function and additional logs only at important failure or warning exit points. For vague optimize, clean up, or refactor requests, only enforce these rules and apply behavior-preserving micro-optimizations. Return a single Python code block with no explanations.

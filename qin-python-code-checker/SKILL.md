---
name: qin-python-code-checker
description: Use for Python writing and formatting tasks across projects when Codex generates, writes, formats, rewrites, refactors, cleans up, optimizes, or otherwise edits Python modules, classes, functions, scripts, or tests. Enforce a minimal Python formatting and refactoring guide so output stays concise, production-ready, behavior-preserving by default, aligned with single-line signatures and calls, descriptive naming, top-level imports, limited try/except usage, trusted function contracts without repeated type or value checks, no unnecessary guards, preserved manual formatting, no auto-formatters unless explicitly requested, the exact required logging pattern, and code-only output when the user wants raw Python.
---

# Qin Python Code Checker

## Overview

Apply the Python coding rules in [references/python-style-guide.md](references/python-style-guide.md) whenever you generate or edit Python code. Treat this skill as required for Python write tasks when the user wants this minimal style, and treat that reference as the source of truth for formatting, naming, logging, and cleanup behavior.

## Trigger

Use this skill whenever the user wants Python code written or cleaned up in this minimal style, including:

- new Python modules, classes, functions, scripts, or tests
- formatting or style cleanup without behavior changes
- refactors, optimize, clean up, or improve requests that should stay behavior-preserving
- direct snippet rewrites where the user wants raw Python back

## Workflow

1. Read the existing Python file or requested snippet first and preserve behavior unless the user explicitly asks for new behavior.
2. Read [references/python-style-guide.md](references/python-style-guide.md) before making Python edits or generating new Python code.
3. Apply the guide directly instead of layering generic style advice on top of it.
4. Preserve the existing manual formatting style of the touched Python file unless the user explicitly asks for reformatting.
5. Do not run `ruff format`, `black`, or any other auto-formatter unless the user explicitly asks for it.
6. For vague requests such as "optimize", "clean up", "refactor", or "improve", treat the task as style enforcement plus behavior-preserving micro-optimization only.
7. Return only the code when the user asks for Python output unless they explicitly ask for explanation.
8. For normal bug fixes and update requests, fix the source function, prompt, or code path directly instead of stacking wrapper flows, fallback branches, or extra logic layers on top.
9. If the direct fix becomes a large structural rewrite, stop and ask with a short plan before changing the architecture.

## Non-Negotiables

- Keep function signatures and function or method calls on one line when reasonably possible.
- Use descriptive full-word names and inline single-use values.
- Use correct English spelling for new Python identifiers, function names, class names, keys, comments, and prompt labels even when the user request contains typos, unless an existing external API, persisted schema field, third-party contract, or compatibility boundary requires the misspelling.
- Avoid vague placeholder names such as `out`, `result`, `data`, `item`, `value`, or `response` when a more specific meaning is known.
- Do not add one-off class helper methods that are only called by one other method.
- Do not add trivial module-level helper functions that only wrap a small expression, path join, normalization step, or predicate used by one local flow.
- Do not split one method into private `__prepare_*`, `__merge_*`, `__build_*`, or `__get_*_helper` wrappers when those helpers have exactly one caller; inline the logic into the real method instead.
- Do not add one-line predicate wrappers such as `_is_artwork_type(...)` when a direct inline comparison is clearer at the actual call site.
- If a helper body is very simple, call the code directly at the real use site instead of creating a helper just to reuse a few short lines.
- Do not keep broken or awkward source logic in place and add another wrapper, retry-only branch, or compatibility layer on top when the underlying function can be fixed directly.
- Keep imports at the top of the file.
- Use at most one `try`/`except` per function.
- Keep `try`/`except` scopes narrow. Leave straight-line merge, transform, and return code outside the `try` when only one call actually needs protection.
- One-line policy: when an `except` branch only logs and returns or raises, keep the log call on one physical line and inline any single-use error formatting instead of creating a temporary variable.
- Trust declared function inputs and return shapes instead of repeatedly rechecking `dict`, `list`, `int`, or similar types across call sites.
- Do not add fallback/default/compatibility branches, alternate input aliases, empty-value substitutes, or caller-side repair logic unless the user explicitly asks for them or a real external API contract requires them.
- When the requested change is case A, write code for case A only; do not add branches, comments, or validation for unrelated cases B/C/D unless the user named them or an existing contract requires them.
- Do not validate, repair, or branch on a called function's return format at the caller. If the returned shape is wrong, fix the producing function, helper contract, or prompt instead of adding caller-side format checks.
- If an AI helper is already asked to return structured JSON through its own contract such as `json_root="object"` or `json_root="array"`, trust that parsed result and do not add `json.loads`, `ast.literal_eval`, string fallbacks, or repeated `isinstance` parsing at the call site.
- For AI-driven extraction, naming, or review flows, do not add local keyword filters, special-case semantic validators, or format-based decision logic for the AI content; put those rules in the prompt and keep local code limited to minimal schema normalization.
- Preserve the existing manual formatting style of the file, and do not run auto-formatters unless the user explicitly asks.
- Use a plain `if`/`else` for exactly two mutually exclusive outcomes, and use Python `match`/`case` for three or more outcomes.
- Do not write or keep `if`/`elif` chains for three or more outcomes; for complex predicates that are not one selector, use `match True` with guarded `case _ if ...` branches.
- Do not add guards, demos, TODOs, unused imports, or placeholder logic unless requested.
- Use the exact logging call required by the reference whenever logging is part of the code.

## Guardrails

- Preserve existing behavior unless the user explicitly asks for a functional change.
- Do not force class wrappers, `__main__` blocks, or other structural rewrites unless the code actually needs them; three or more outcomes do need `match`/`case`.
- Do not replace repo-local or user-provided Python rules with broader generic style advice.
- Do not run auto-formatters unless the user explicitly asks for them.

## Reference

- Read [references/python-style-guide.md](references/python-style-guide.md) for the full guide before making Python edits.

## Examples

- "Clean up this Python helper without changing behavior."
- "Format this Python snippet to the minimal house style."
- "Refactor this module, keep the logging pattern, and return only the code."

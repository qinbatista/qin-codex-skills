# Plain C# rules

Use `execution_domain=csharp` for non-Unity C#. These rules apply to ordinary libraries, services, tools, and tests. Unity-specific lifecycle, serialization, main-thread, and asset rules belong in `unity-csharp-rules.md`; Unity work uses `execution_domain=unity_csharp` and reads both files.

- Preserve the repository's local style and public behavior.
- Keep fields private by default; use clear full-word names and underscore-prefixed private fields/locals when that matches the surrounding code.
- Keep one-statement `if` expressions on one line without braces; use braces for multi-statement blocks.
- Use `switch` or a switch expression for three or more outcomes instead of long `else if` chains.
- Keep calls and log calls on one line unless the project style explicitly requires wrapping.
- Avoid one-use helpers and new abstractions unless they make the requested behavior clearer or are required by the existing design.
- Preserve exception behavior, ordering, side effects, async/threading semantics, and public contracts unless the request changes them.
- Keep changes surgical. Before presentation, run exactly one smallest safe local smoke when the changed function is light. For API, large-file, expensive-build, Unity-runtime, or side-effect-heavy work, skip the heavy producer run and check syntax plus changed method, variable, namespace, and direct-reference names. Present `CODE READY` immediately; do not run broad builds, full lint, rendered UI, logs, or regressions first. Every durable C# change emits `ending-required`; `intentionally_skipped_simple_task` is non-code-only. Create one Spark-xhigh-controlled global projectless Ending containing the explicit real build, test, Unity-runtime, or integration checks. Use exact `create_thread` target `{"type":"projectless"}` and require `list_threads` readback with `projectId=null` or absent; project/current-task/subtask placement is BLOCKED. The controller may use saved Terra/Sol `ENDING_CHECK_WORKER` nodes for semantic runtime, code-quality, UI, or visual evidence; those workers never edit or repair. Only Spark availability/capability failure permits Luna-low. All required checks must PASS; FAIL or acceptance mismatch sends the exact repair prompt to the immutable origin session, which performs the authorized repair and starts a fresh Spark-first Ending, for at most three attempts.

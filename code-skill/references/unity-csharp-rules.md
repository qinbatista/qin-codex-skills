# Unity C# Rules

This is the common C# style reference. Unity-specific architecture and lifecycle rules apply to Unity projects; other C# work uses its actual runtime. The routing aliases `csharp` and `c#` resolve to `unity_csharp` for compatibility and do not create another writing profile.

Use [code-writing philosophy](code-writing-philosophy.md) for general ownership, direct calls, result ownership, naming, and scope. Project-specific Skills add their APIs and feature contracts rather than copying these rules. Honor current user instructions and preserve serialized/public compatibility.

## C# style

- Keep a clear self-contained statement or expression on one physical line, including calls, logs, constructors, initializer entries, and ternary assignments. Do not stack constructor arguments vertically when they fit. Wrap only when clarity, correctness, or tooling requires it.
- A single-statement `if` stays on one line without braces; use braces for multiple statements.
- Use `if`/`else` for two outcomes; use `switch`/`case`, switch expressions, or guarded cases for three or more when they express the same behavior.
- Inline a single-use value when readable. Avoid helpers used only once unless they remove real complexity; an `Update()` helper may clarify per-frame flow. Do not create another script for a tiny structural convenience.
- Use an explicit concrete type instead of `var` when known. Keep `var` for unavailable or genuinely noisy concrete types with clear ownership.
- Default fields to `private`; use underscore names for private fields and internal locals, with full words. Prefer properties when exposure is required. Do not use the `internal` access modifier unless the user explicitly requests it.
- Use established `Awake()`/`Start()` initialized values directly rather than repeatedly guarding impossible states.
- Await or own Tasks; `_ = SaveDataAsync();` hides completion and exceptions. Tuple discard bindings are also disallowed; pattern wildcards such as `case _:` remain valid.

## Unity categories

Read only the categories that materially match the task:

| Surface | Reference |
| --- | --- |
| Gameplay ownership, data flow, or pattern choice | [Game code structure](unity-game-code-structure-design.md) |
| Callbacks, lifetime, events, async/main thread, physics, or serialized data | [Lifecycle and serialization](unity-lifecycle-and-serialization.md) |
| Public service API, initialization, cloud, or optional SDK/provider | [Service integration](unity-service-integration.md) |

Gameplay's core is local GameObject behavior in Controllers, feature-wide lifecycle coordination in single-instance Managers, and authored tuning in ScriptableObjects. Detailed structure rules live in the structure reference. Domain Skills own concrete system names, topology, Addressables lifetime, Job/native-container boundaries, feature state, and recorded exceptions.

For verification, follow the active task's smallest convincing check. A focused reference/style check does not prove Unity runtime behavior; never start or compile the whole project unless requested.

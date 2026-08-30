# Unity C# rules

Use the single active `execution_domain=unity_csharp` profile for all new C# work. The language aliases `csharp` and `c#` resolve here; the former plain `csharp` domain is history-only and must not create a second rule path. Every Unity C# writing node reads this file after the universal [`code-writing-philosophy.md`](code-writing-philosophy.md). A project may refine paths, bootstrap, naming, and tighter ownership, but it cannot silently weaken these common rules.

Project-specific Unity Manager, gameplay, SDK, or business-domain Skills may add only their domain facts and APIs. They always inherit this common profile and must not duplicate, fork, or compete with its base C# writing, direct-call, lifecycle, or serialization rules.

Apply these rules for Unity projects and C# code, including MonoBehaviours, ScriptableObjects, managers, gameplay systems, runtime scripts, reviews, explanations, refactors, and performance work.

## Category router

Always apply this common file. Then load only the categories materially matched by the task; load more than one when the task genuinely crosses categories.

| Task surface | Additional reference |
| --- | --- |
| ownership, architecture, Controller/Manager/ScriptableObject boundaries, patterns, factories, pools, state, command, observer | [`unity-game-code-structure-design.md`](unity-game-code-structure-design.md) |
| MonoBehaviour callbacks, scene/prefab lifetime, components, events, coroutines, async/main thread, physics timing, serialization | [`unity-lifecycle-and-serialization.md`](unity-lifecycle-and-serialization.md) |
| Unity Gaming Services, cloud/auth/analytics, Addressables service, SDK/provider selection, service initialization | [`unity-service-integration.md`](unity-service-integration.md) |

An ordinary local C# edit with none of those surfaces loads no category file. The Code Gate announces the common rules and matched categories before source inspection or editing.

## Shared and consumer boundary

This reference owns concise, reusable Unity C# writing rules and category routing. A consuming game Skill loads this common profile and its matched categories first; it must not repeat the Controller/Manager/ScriptableObject core, generic lifecycle guidance, C# style, direct-call rules, or provider boundary.

A consuming game Skill adds only concrete game contracts that this reusable profile cannot decide: its named system owners, fixed-membership or pool topology, Addressables instance lifetime, centralized Job/native-container boundary, feature-state handoff, and explicitly recorded exceptions. Keep each stricter consumer invariant once in that consumer Skill, with its current-system record as the concrete authority.

## Workflow

1. Read repo-level `AGENTS.md`, local style notes, or direct user instructions, and let tighter local rules override this shared style.
2. Preserve core behavior unless the user explicitly asks for a functional change.
3. For optimize, simplify, or cleanup requests, keep edits inside the requested code path unless the user explicitly asks to broaden scope.
4. When independent repeated work is present or discovered during optimization, also read `references/parallelization.md`; parallelize only pure data work that preserves Unity main-thread rules and the same observable result.

## Output

- Return the final updated C# code first when the user asks for code.
- Then briefly explain what changed and why in 1-3 short sentences unless the user asks for code only.

## Unity Structure

- Keep GameObject-bound local behavior in named Controllers, feature-wide lifecycle coordination in single-instance Managers, and authored/tunable feature data in the owning ScriptableObject contract. This compact core applies to every Unity gameplay edit; load the detailed structure category before changing ownership or selecting a pattern.
- Patterns solve a demonstrated lifecycle or coordination need; they are never required ceremony. A direct call remains the default until queueing, multiple consumers, product variants, bounded reuse, or complex transitions are real.

## C# Style

- Keep every self-contained Unity C# statement or expression that fits clearly on one physical line on one physical line, including declarations, assignments, returns, conditions, calls, logs, constructors, object creation, initializer entries, and ternary expressions. Do not vertically wrap code that fits or split a ternary assignment only to indent its branches; wrap only when it cannot fit without harming readability, correctness, or tooling, or when explicitly requested.
- For a single statement, keep the entire `if` on one line without braces.
- Use braces only when the block contains more than one statement.
- Use plain `if`/`else` for exactly two mutually exclusive outcomes.
- Use `switch`/`case`, a switch expression, or guarded switch cases for three or more outcomes.
- Do not write or keep `if`/`else if` chains for three or more outcomes when C# can express the same behavior with `switch`.
- Inline a value when it is used exactly once and remains readable.
- Do not create helper functions that are only used once, except `Update()` may call one helper used only there when it makes the per-frame flow clearer.
- Do not create a new C# script only to simplify a very small or easy structure.
- Keep function calls and log calls on one line.
- Keep constructor calls and object-creation expressions on one physical line, including long argument lists. In collection, property, and array initializers, keep each `new Type(...)` entry flat; never format it as `new Type(` followed by vertically stacked arguments. For example: `new InAppPurchaseProduct(ProductId.Coin500.ToString(), "coins_500_ios", "coins_500_android", 500, 3.99m, "USD", InAppPurchaseProductKind.Consumable),`
- Keep spaces after commas.
- Do not fold argument lists across multiple lines unless explicitly requested.
- Use an explicit concrete type instead of `var` when the type is known at the declaration. Keep `var` only when the concrete type would be genuinely noisy or unavailable and the initializer still makes ownership unambiguous.

## Direct calls and result ownership

- Do not assign a return value or `Task` to `_`. In particular, `_ = SaveDataAsync();` is forbidden because it hides completion and exceptions. Await the task or keep it in a named owned field with cancellation and exception observation.
- Discards in tuple deconstruction are also forbidden for newly written code. Access the required member directly or change an owned producer contract. Pattern wildcards such as `case _:` are allowed because they do not bind and discard a runtime value.
- Do not write a method whose only behavior is calling another method with the same arguments and return value. Call the real owner once at the call site.
- Never write accidental self-recursion such as `void SaveData() { SaveData(); }`. Intentional recursion requires a visible base case and progress toward it.
- A public facade, adapter, or provider method is allowed only when it adds public compatibility, validation, translation, transaction, lifecycle, platform, SDK, or provider-selection semantics. Its name alone does not justify another call layer.

## Fields And Names

- Default fields to `private`.
- Use underscore names for internal fields and internal locals, such as `_name`, `_currentY`, `_index`, `_offset`, `_damageValue`, `_randomSeed`, and `_enemyHealth`.
- Use clear full-word names instead of abbreviations like `dmg`, `rs`, or `hp`.
- Do not declare public fields by default.
- If something must be exposed, prefer a property with `get; set;`.
- If a field or value is initialized in `Awake()` or `Start()`, use it directly instead of adding repeated guards like `!= null` or `> 0`.

## Quick Check And Detached Ending

- Keep changes surgical. Before presentation, run exactly one smallest safe local smoke when the changed function is light. For API, large-file, expensive-build, Unity-runtime, or side-effect-heavy work, skip the heavy producer run and check syntax plus changed method, variable, namespace, serialized field, and direct-reference names.
- Before final Ending or release-gate PASS, run `code-skill/scripts/code_rule_guard.py --diff-from HEAD` on changed `.cs` files so new discard assignments, same-argument pass-through wrappers, only-action self-recursion, obvious `var = new Type(...)`, and avoidable vertical calls fail deterministically without rewriting unchanged legacy code.
- Present `CODE READY` immediately after the Quick Check. Non-trivial Unity C# changes are material and require one global projectless Ending plus durable project-memory closeout; only explicit `trivial_value_only` work with no other surface may skip and records `ending_skip_reason=no_real_test_or_information_or_memory_or_material_update`.
- Create one global projectless Ending and prove null placement through `list_threads` with `projectId=null`. Spark is first; a durable quota/five-hour/provider cooldown selects the next stronger supported controller until expiry. Capability-routed Terra/Sol `ENDING_CHECK_WORKER` nodes may collect semantic Unity evidence. All required checks must PASS. Failure creates an independent projectless Repair Task that never contacts or interrupts existing sessions and waits for active write ownership before repair and a fresh parent-linked Ending.

## Guardrails

- Do not add abstractions, wrappers, lifecycle changes, data-flow changes, or defensive checks for impossible states unless requested.
- Do not change multiple authoring, manager, or system scripts when the user asked only for local optimization; report the broader issue or ask before expanding scope.
- Do not let broader generic C# formatting advice override this style.

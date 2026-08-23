# Unity Game Code Structure Design

Load this Unity C# category when a create, edit, repair, refactor, or test node materially changes gameplay ownership, data flow, Controller/Manager/ScriptableObject boundaries, or pattern selection, including a node owned by another Unity Skill. Read the nearest project `AGENTS.md` first, then this file before choosing files, ownership, data flow, or patterns. The compact Controller/Manager/ScriptableObject core in `unity-csharp-rules.md` still applies to every gameplay edit; this file supplies the detailed structure decision. A project may refine paths, bootstrap, naming, and stricter constraints, but it cannot silently weaken the Controller/Manager/ScriptableObject core below. Only an explicit current user instruction may authorize a scoped exception. Do not apply this category to non-game Unity tooling such as Editor windows, importers, build tooling, asset processors, test fixtures, or one-off migration tools.

## Ownership and lifecycle

1. The only gameplay runtime-behavior roles are a clearly named `XXController` and a clearly named `XXManager`. Do not introduce a third `System`, `Service`, `View`, `Presenter`, `UI`, or helper `MonoBehaviour` when the responsibility belongs to one of these roles. Data-only ScriptableObjects, serializable records, enums, interfaces, Editor tools, and tests are not runtime-behavior roles.
2. A repeatable, GameObject-bound local behavior belongs to an `XXController`. Its scope is one GameObject or one explicitly independent responsibility on that GameObject. Keep that responsibility's bindings, local presentation, input, movement, physics, and cleanup together when they are truly one concern.
3. A feature-wide lifecycle boundary belongs to one single-instance `XXManager` for that feature. The Manager is the feature-level data source and owns bootstrap, registration, shared data flow, creation, destruction, pooling, reuse, release, and group coordination. Singleton semantics follow the project's bootstrap and teardown contract; `Singleton` never justifies hidden mutable globals or a global dependency shortcut.
4. After a Manager spawns or hands off a Controller, the Controller operates autonomously. The Manager coordinates it again only for a real feature-wide concern such as pooling, global pause, shared selection, global position, group state, or release. Do not make the Manager drive every local update.
5. Keep unrelated Controller concerns separate. A GameObject may have more than one Controller only when their responsibilities are independently named and independently changeable, such as `PlayerMovementController` and `PlayerSkillController`. Do not fuse unrelated behavior or split one simple local behavior into ceremony classes.
6. Reuse the current project's structure, nearby ownership examples, lifecycle rules, and `AGENTS.md` before introducing a new type. Make the minimum coherent change and preserve Unity main-thread, Addressables, serialized-reference, and cleanup boundaries.

## Authored data versus runtime state

- Every Manager functional or tunable parameter, especially every value or prefab used to configure or create Controllers, comes from the feature's ScriptableObject-owned data contract. A Manager serializes ScriptableObject references only; it does not keep its own authored tuning fields. Controllers receive configuration through their Manager or the established local data flow and do not duplicate feature tuning.
- A Manager may retain internal transient implementation state: runtime observations, cached component references, IDs and handles, counters, registries and collections, pool queues, active instances, subscriptions, and method parameters or per-call locals. These are implementation state, not authored tuning.
- A Controller may serialize only the GameObject, component, or UI bindings required to control its own object. Its tunable behavior and feature content still come from the owning ScriptableObject data.
- Immutable language constants, protocol keys, shader/property names, enum members, and compile-time limits do not need ScriptableObjects. Do not turn a constant into an asset merely to satisfy this rule.
- ScriptableObjects are authored/shared configuration by default, not mutable save data or a hidden runtime singleton. A project may explicitly define a different data owner; follow that tighter contract.
- Reuse the project's existing canonical ScriptableObject location. If none exists, create one coherent data location instead of scattering assets or data types across feature folders.

## Project continuity

- Keep the full process and pattern contract here in the global Skill. A project `AGENTS.md` may carry a compact reiteration, local paths, bootstrap rule, checker, and canonical project-doc pointer; deleting that reiteration later does not disable this global gate.
- If a Unity project has no structural `AGENTS.md` guidance, add a compact observed contract only when the task is authorized to change project files. Do not turn `AGENTS.md` into a task log or copy this entire reference into it.
- This reference governs the writing process. `project-memory-skill` records only the sanitized verified result after Ending; result memory never replaces this process gate.

## Pattern decisions, not ceremony

Use a pattern only when its concrete decision trigger exists. Patterns solve a demonstrated lifecycle or coordination need; they are never required ceremony. The reference point is *Level up your code with design patterns and SOLID*, “Design patterns for game development,” pp. 48-101, together with the project's current Unity APIs and source. The book provides decision vocabulary; current project contracts and APIs win.

| Pattern | Use when | Keep simpler when |
| --- | --- | --- |
| Factory | Several product variants need a common construction policy | One stable prefab or Addressables load is enough |
| Object Pool | Repeated short-lived create/destroy work is measured or bounded reuse is required | Lifecycle is infrequent or a bounded pool is not justified |
| State | Transitions and per-state behavior have outgrown a small enum/switch or Animator graph | The state set is small and stable |
| Command | Requests need queueing, replay, undo, serialization, routing, or deferred execution | A direct, immediate single-owner method call is clear |
| Observer | One publisher has multiple independent consumers | One feature-local consumer can use a direct dependency |
| Prototype | A configured object needs copy semantics beyond Unity prefab instantiation | Prefab or Addressables instantiation already expresses the copy |
| Singleton | One feature genuinely needs global lifetime and coordination | A local Controller, injected reference, or feature boundary is sufficient |

For pooled objects, one Manager owns acquire, reset, release, capacity, and shutdown together. For observers, define subscribe and unsubscribe with the Unity lifecycle. For every pattern, choose the least additional type and allocation needed for the demonstrated behavior.

## Conflict precedence and explicit exceptions

Apply rules in this order: direct current user requirement; this global Controller/Manager/ScriptableObject core; tighter project `AGENTS.md` and local feature details; existing serialized/public runtime compatibility; generic C# style. A project refinement may tighten or locate the core, not silently replace it. A scoped exception must name its owner and why it is necessary.

The following are explicit exceptions, not rule violations: non-game Unity tooling; data-only ScriptableObjects and serializable records; immutable constants; runtime observations; cached component references; IDs/handles; counters; collections/registries; pool state; and per-call locals. Existing legacy code outside the changed scope is evidence, not permission for an unrequested rewrite.

## Positive and negative examples

Positive — a `DamageNumberManager` reads number style and duration from `SODamageNumberData`, takes/recycles the visual object, and registers its active instances. `DamageNumberController` owns the spawned GameObject's animation and local reset, then returns itself through the Manager-owned release path.

Positive — `PlayerMovementController` and `PlayerSkillController` may share a GameObject because movement and skill activation are separately named, independently changing responsibilities. Neither becomes a feature-wide registry or pool owner.

Negative — a `CombatService` MonoBehaviour that both tunes enemy damage and updates every enemy is a third runtime role plus mixed ownership. Fold local behavior into the appropriate Controller and shared lifecycle into the approved Manager.

Negative — a Controller with serialized `speed`, `duration`, and damage values duplicates feature tuning. Move authored values to the owning ScriptableObject and pass the resolved configuration through the existing Manager boundary.

Negative — wrapping a single immediate method call in Command, Observer, Factory, and State objects because their names appear in a pattern catalog. Keep the direct call until queueing, multi-consumer notification, variants, or complex transitions are real.

Negative — `void SaveData() { SaveData(); }`, or a `SaveData()` wrapper whose only body is `_saveProvider.SaveData()` with identical arguments and return semantics. The first is accidental recursion; the second is an unowned pass-through. Call the real owner directly unless the public boundary adds validation, translation, transaction, lifecycle, platform, SDK, or provider-selection behavior.

## Validation checklist

- The changed GameObject behavior has one named Controller owner, and unrelated responsibilities are not fused or ceremonially fragmented.
- The Manager's single-instance lifecycle boundary matches project bootstrap; it owns group creation, pooling, and release without micromanaging handed-off Controllers.
- Tunable feature behavior comes from ScriptableObject data, while transient implementation state remains local to the runtime owner.
- Pattern choice has a concrete trigger and preserves lifecycle cleanup, subscription hygiene, allocation discipline, and Unity main-thread rules.
- Project structural checks and the smallest relevant Unity compilation are selected by the local project contract; documentation-only work does not pretend to prove a Unity runtime change.

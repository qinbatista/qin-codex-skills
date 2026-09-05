# Unity Game Code Structure

Use for Unity gameplay ownership, data flow, and pattern decisions. Read current project structure and relevant project memory first. These are general code-organization preferences, not feature recipes. They do not apply to Editor windows, importers, build tools, asset processors, tests, or migration utilities.

## Ownership

- Gameplay runtime behavior belongs to named `XXController` or `XXManager` roles. Avoid a third helper MonoBehaviour role when one of these already owns the responsibility. Data records, enums, interfaces, and ScriptableObjects are not runtime-behavior roles.
- A Controller owns one GameObject-bound local responsibility, including its bindings and cleanup. Multiple Controllers may share an object when their concerns are independently named and changeable.
- One single-instance Manager owns a feature's bootstrap, registration, shared data flow, creation, pooling, release, and group coordination. Its singleton lifetime follows project bootstrap and teardown; it is not a shortcut to hidden mutable globals.
- After handoff, Controllers operate autonomously. Managers re-coordinate only real shared concerns such as pooling, global pause, selection, group state, or release; they do not drive every local update.

## Data

- Every Manager authored functional or tunable parameter comes from its feature's ScriptableObject data contract. A Manager serializes ScriptableObject references only.
- Controllers may serialize GameObject/component/UI bindings needed for their own object. Feature tuning comes through the Manager or established data flow, without duplicate authored values.
- Transient runtime state stays with its owner: observations, cached references, IDs/handles, counters, registries, collections, pool state, subscriptions, and per-call values.
- Immutable constants, protocol keys, shader names, enums, and compile-time limits need no ScriptableObject. Configuration assets are not accidental save files or hidden runtime singletons.
- Reuse the project's canonical ScriptableObject location and preserve main-thread, Addressables, serialization, and cleanup contracts.

## Patterns

Use patterns only for a demonstrated coordination or lifecycle need:

| Pattern | Decision trigger |
| --- | --- |
| Factory | Multiple product variants need a shared construction policy |
| Object Pool | Bounded reuse is needed or repeated creation/destruction is measured |
| State | Transitions outgrow a small enum/switch or existing Animator graph |
| Command | Queueing, replay, undo, serialization, or deferred execution |
| Observer | One publisher has multiple independent consumers |
| Prototype | Copy semantics beyond prefab/Addressables instantiation |
| Singleton | A real feature-wide lifetime and coordination owner |

Otherwise retain direct calls and the existing owner. A pool has one owner for acquire, reset, release, capacity, and shutdown; an observer has explicit subscribe/unsubscribe lifetime.

## Continuity

Current user instructions can change these preferences. Project rules refine paths, bootstrap, naming, and stricter constraints; preserve public/serialized compatibility and document a necessary scoped exception. Keep only stable local ownership and entry points in `AGENTS.md`, and concise verified project facts in memory. Do not copy this reference or a task log into either place. Verify ownership/data changes through focused checks during the active task; documentation edits do not prove runtime behavior.

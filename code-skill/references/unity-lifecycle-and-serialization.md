# Unity C# Lifecycle And Serialization

Load this category only when the Unity C# task materially touches MonoBehaviour callbacks, scene or prefab lifetime, components, events, coroutines, async work, physics timing, or serialized data. The mandatory common writing rules remain in [`unity-csharp-rules.md`](unity-csharp-rules.md).

## Callback ownership

- Use `Awake()` for state and component references owned by the same object. Make initialization idempotent when domain reload, prefab reuse, or explicit reinitialization can repeat it.
- Use `OnEnable()` and `OnDisable()` as a symmetric pair for subscriptions, callbacks, input actions, and enable-scoped resources. Do not subscribe twice or rely on `OnDestroy()` to repair an `OnDisable()` leak.
- Use `Start()` only for work that genuinely depends on another object's completed `Awake()` or on an explicitly initialized service. Do not rely on accidental script execution order; configure the order or expose an explicit initialization dependency when order is contractual.
- Read input and advance ordinary frame state in `Update()`, perform Rigidbody physics in `FixedUpdate()`, and perform camera/follow corrections in `LateUpdate()` when those timings are material.
- Stop owned coroutines, cancel owned asynchronous operations, release native or pooled resources, and detach long-lived callbacks at the lifecycle boundary that acquired them.

## Async and main-thread safety

- Do not write `_ = SomeTask()` or use `async void` for background ownership. Unity event callbacks are the narrow `async void` exception; catch and surface their failures at that boundary.
- Await work when the caller owns completion. Otherwise store the `Task` in a named field, attach cancellation to the owning object's lifetime, and observe completion and exceptions.
- Resume Unity-object access on the Unity main thread. After an await, confirm the owning lifecycle is still active before touching destroyed objects or scene state.

## Serialization and authored data

- Prefer `[SerializeField] private ConcreteType _field;` for Inspector bindings. Do not expose public mutable fields merely for serialization.
- Preserve serialized field compatibility. Use Unity's supported rename migration when an existing serialized name changes; do not silently orphan prefab or scene data.
- Treat ScriptableObjects as authored/shared configuration unless the project explicitly owns mutable runtime state there. Do not use a mutable ScriptableObject as an accidental save file or hidden singleton.
- Cache stable component references outside per-frame callbacks. Do not repeat `GetComponent`, allocation, reflection, LINQ enumeration, or string construction every frame when the same value can be retained safely.

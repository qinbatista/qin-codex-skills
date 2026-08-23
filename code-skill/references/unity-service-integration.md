# Unity C# Service Integration

Load this category only when the Unity C# task touches Unity Gaming Services, cloud save, authentication, analytics, Addressables services, a platform SDK, provider selection, or initialization exposed across a public game API. The mandatory common writing rules remain in [`unity-csharp-rules.md`](unity-csharp-rules.md).

## Stable boundary

- Keep the path `public facade -> neutral interface -> selected provider -> optional SDK`. Public game code depends on the neutral contract; provider and SDK types stay behind the selected implementation.
- A facade is allowed only when it owns real public compatibility, validation, state translation, lifecycle, or provider selection. If it merely calls another method with the same arguments and return value, remove it and call the real owner once.
- Keep initialization explicit with observable states such as uninitialized, initializing, ready, and failed. Coalesce concurrent initialization, reject or queue calls according to the declared contract, and do not initialize the same SDK from multiple owners.
- Forward each callback or operation once. Avoid duplicate event bridges, duplicate save calls, nested manager-to-manager forwarding, and hidden initialization in getters or unrelated methods.

## Optional provider and proof boundary

- The optional SDK assembly may be absent. Keep compile-time provider selection and runtime availability explicit; do not scatter conditional SDK branches through gameplay callers.
- Preserve cancellation, exception, offline, and retry semantics at the provider boundary. Do not add silent fallback providers or report a successful cloud/device operation from local source inspection alone.
- Use a thin test UI only to exercise the public facade. It must not become a second service owner or bypass the neutral interface.
- Claim editor, device, cloud, sandbox, production, or general-availability support only when that exact surface has fresh evidence.

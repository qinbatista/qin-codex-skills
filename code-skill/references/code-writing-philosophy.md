# Code-Writing Philosophy

Apply these preferences before and during code changes in any language. Domain references add only their specific rules.

## Understand the owner

Read the nearest project `AGENTS.md`, relevant same-project memory, existing code, and focused tests. Establish the real input/output contract and the module that owns it. Reuse that owner instead of scattering one responsibility across wrappers, adapters, or fallback branches. Keep `AGENTS.md` limited to stable structure, ownership, entry points, constraints, and definition of done; update it only when those facts change or are missing and useful to the task.

## Write the minimum coherent change

- Preserve unrelated behavior and local conventions. Add only requested behavior and remove only complexity made obsolete by the change.
- Call the real owner directly. A method forwarding the same arguments and return value adds no useful boundary. A facade is justified by actual compatibility, validation, translation, transaction, lifecycle, platform, or provider semantics. Avoid accidental self-recursion such as `SaveData() { SaveData(); }`; intentional recursion needs progress and a base case.
- Own every result and asynchronous operation. Do not assign or unpack into `_` merely to hide a result, and never use `_ = SomeTask()` for silent fire-and-forget. Await work or retain a named task with cancellation, completion, and exception handling. Pattern wildcards such as `case _` remain valid.
- Keep a complete statement, expression, signature, call, constructor, or literal on one physical line when clear and compatible with tooling. Wrap only for real readability, correctness, or tool limits; do not minify unrelated logic.
- Use descriptive full-word names. Correct unambiguous English spelling at new naming boundaries; preserve external/public/persisted names or supply the required migration. For a rename, update declarations and direct references and report the original-to-canonical mapping. Do not rewrite quoted user data or third-party names.
- Trust established inputs and outputs. Fix an owned producer instead of layering speculative aliases, parsing, defaults, or caller-side repair. Add validation at genuine external or untrusted boundaries.

## Check what changed

Consider bounded memory use, CPU/repeated work, disk retention, resource cleanup, concurrency/event subscriptions, and long-running behavior where relevant. Verify the changed path in the active task; record what was observed and what remains unproven. Ending distills durable project facts and preferences from this evidence, not task history or speculative architecture.

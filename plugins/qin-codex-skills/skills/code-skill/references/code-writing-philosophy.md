# Code-Writing Philosophy

Apply these preferences before and during every local code change in any language, including tests and scripts. Domain references add only their specific rules.

## Understand the owner

After the project startup gate, follow [AI-index code navigation](../../management-skill/references/project-ai-index.md#code-navigation): module → file → method or stable anchor → necessary dependencies. Recall the corresponding same-project memory, then confirm the current implementation. Start with the affected method or bounded block and expand only far enough to understand inputs, outputs, state, side effects, error handling and the relevant caller/test contract. A fragment without its controlling conditions is not enough; reading every neighboring method is not the default. Reuse already-read unchanged context within the task. On a missing or stale route, perform a bounded symbol search in the selected owner and repair its verified route instead of rereading the repository.

Keep each responsibility in its owning module with explicit entry points and narrow dependencies. Reuse that owner instead of scattering one operation across wrappers, adapters, or fallback branches. Maintain touched stable methods/anchors, contracts and justified logic-chain links in the project index so later tasks can repeat this targeted read. Store historical decisions and source-bound outcomes in project memory; do not duplicate source bodies, line-number-only locations or changing evidence in the index. Keep root `AGENTS.md` limited to stable structure, ownership, entry points, constraints, and definition of done.

## Place code by responsibility

For each changed behavior, identify the public entry point, the module that owns the rule, and the callers that depend on it. Choose names that let a maintainer trace that path from the file tree. A module can be one file. Give a feature a folder when several files implement the same capability and usually change together. Follow established framework locations for models, commands, migrations and tests, keeping the same owner identifiable across those locations.

| What you are placing | Where it belongs |
| --- | --- |
| Business rule or operation | In its feature module. Expose the operation callers need and keep implementation details private. Other features call its public contract. |
| Model, validation or persisted representation | With the module that defines the data's meaning and invariants. Reuse its canonical type. Move a contract into a shared module only when independent callers rely on the same meaning. |
| Command, job or integration script | At the project's entry point for that tool. Parse external input, call the owning operation and translate its result. Keep business decisions in the owner so other entry points can reuse them. |
| Function | Beside the operation or model whose contract it serves. Give an independently testable rule explicit inputs and outputs. Keep I/O and mutable state with the code that owns those effects. Apply the method criteria below before extracting a helper. |

For example, in a library with two capabilities, `loans/model.py` might own a loan's due date and `loans/renew.py` its renewal rules. A single `catalog.py` can own title lookup. A `cli.py` dispatches to their public operations. Changing the renewal limit should require edits only to the loans owner and its relevant tests. A change to a public contract can also require edits to its callers.

Verify placement through use. Exercise the normal entry point, then run the affected rule with representative inputs through its module API where one exists. For an isolation change, also exercise a sibling feature and inspect the diff for edits outside the intended owner. Trace any such edit to an actual caller or contract.

## Choose method boundaries deliberately

Prefer completing one cohesive operation in one method. Opening a player and reading its content can be one operation with one resource lifecycle; a one-use image conversion step alone is not a reason to extract a helper. For variants with the same flow, such as opening different browsers, prefer meaningful parameters to near-identical methods. Preserve genuinely different platform/provider contracts rather than hiding them behind speculative flags.

Create a method when it has a distinct responsibility with little overlap, meaningful reuse by real callers, or a necessary validation, compatibility, transaction, lifecycle or provider boundary. Its name and contract should explain why it can be understood and changed independently. Do not extract merely to shorten a method, name a single expression, or add a forwarding layer. Equally, do not merge unrelated operations into an oversized method or force independent contracts into one parameter-heavy function. Prioritize a correct, complete, cohesive change; there is no token, method-count or reading-line quota.

When existing code obstructs this workflow, identify the concrete coupling, duplicated flow or fragmented operation and its affected files/methods. Propose the new ownership and method boundaries, explain how they make the operation independently understandable and preserve behavior, and specify a real before/after acceptance check. Ask whether to perform a structural refactor unless that exact refactor is already authorized; continue the scoped requested work where possible. After approval, verify the affected behavior and failure/resource boundaries, update the navigation links, and report the actual result. File length alone is not a defect, and index maintenance alone does not authorize a refactor.

## Write the minimum coherent change

- Preserve unrelated behavior and local conventions. Add only requested behavior and remove only complexity made obsolete by the change.
- Call the real owner directly. A method forwarding the same arguments and return value adds no useful boundary. A facade is justified by actual compatibility, validation, translation, transaction, lifecycle, platform, or provider semantics. Prevent accidental self-recursion such as `def save_data(): return save_data()`. Intentional recursion needs progress and a base case.
- Own every result and asynchronous operation. Do not assign or unpack into `_` merely to hide a result, and never use `_ = SomeTask()` for silent fire-and-forget. Await work or retain a named task with cancellation, completion, and exception handling. Pattern wildcards such as `case _` remain valid.
- Keep a complete statement, expression, signature, call, constructor, or literal on one physical line when clear and compatible with tooling. Wrap only for real readability, correctness, or tool limits; do not minify unrelated logic.
- Use descriptive full-word names and follow [correct task names](../../task-analyze-skill/SKILL.md#correct-task-names) in task wording. Correct unambiguous English spelling at new naming boundaries; preserve external/public/persisted names or supply the required migration. For a rename, update declarations and direct references. Do not rewrite quoted user data or third-party names.
- Trust established inputs and outputs. Fix an owned producer instead of layering speculative aliases, parsing, defaults, or caller-side repair. Add validation at genuine external or untrusted boundaries.

## Check what changed

Consider bounded memory use, CPU/repeated work, disk retention, resource cleanup, concurrency/event subscriptions, and long-running behavior where relevant. For async results, object reuse, cached/derived state, configuration handoffs, or retries with side effects, apply [state and side-effect ownership](state-and-side-effects.md). Verify the changed path in the active task, using [code-navigation acceptance](../../management-skill/references/project-ai-index.md#code-navigation); record what was observed and what remains unproven. Ending distills durable project facts and preferences from this evidence, not task history or speculative architecture.

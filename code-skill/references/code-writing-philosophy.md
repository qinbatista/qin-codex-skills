# Code-Writing Philosophy

This is mandatory before/during-writing process authority for every code creation, repair, feature, refactor, or test-writing node in any programming language, including a small edit and code owned by another implementation Skill. An exact-scoped read-only lookup remains outside this gate.

## 1. Establish the current contract

- Inspect the nearest project `AGENTS.md`, then the owning source's current responsibility, style, entry points, and tests before editing.
- Make an explicit `AGENTS.md` continuity decision: if it is absent, lacks stable structure/ownership/entry points/constraints/definition-of-done guidance, or those facts materially change, create or update a compact observed-evidence contract. Keep it free of this full philosophy, task history, results, logs, and speculative architecture.

## 2. Classify ownership and overlap

- Determine whether the request changes existing code, extends an existing owning path, or introduces genuinely new ownership.
- Reuse the existing owner when present. Give each module, file, and type one clear responsibility; do not split it across adapters, wrappers, fallback nests, or scattered branches.

## 3. Write the minimum coherent change

- Choose the smallest coherent change that satisfies the current contract and local style.
- When simplifying the owning path is smaller and clearer, do that instead of layering adapters, wrappers, fallback nests, or scattered branches around awkward code.
- Preserve unrelated behavior and remove only complexity made obsolete by the change.
- Give every produced value and asynchronous operation an explicit owner. Do not assign or unpack into `_` merely to hide an unused result, and never use `_ = SomeTask()` as silent fire-and-forget. Await the operation or retain it in an owned task whose cancellation, completion, and exceptions are observed. A language wildcard such as a pattern-matching `case _` is allowed because it does not bind and discard a runtime result.
- Call the real owner directly. Do not add a method whose only behavior is forwarding the same arguments and return value to another method, and never write accidental self-recursion such as `SaveData() { SaveData(); }`. A facade or adapter is justified only when it adds an actual public compatibility, validation, translation, transaction, lifecycle, platform, or provider boundary.
- Keep a complete statement, expression, signature, call, constructor, or literal on one physical line when it remains clear and compatible with the repository tooling. Wrapping is for genuine readability, correctness, or tool limits; it is not a default style. This is a clarity rule, not permission to minify unrelated logic.
- Prefer explicit names and explicit ownership over placeholders. If a returned member is not needed, call an API that returns the needed value or access the required member directly instead of creating a discard binding.

## 4. Check lifecycle and continuity

- Perform a proportional lifecycle performance pass: bounded memory use, disk growth and retention, CPU cost or repeated work, resource cleanup, concurrency/event subscriptions, and long-running behavior.
- Confirm the final ownership and `AGENTS.md` continuity decision still hold before the normal Quick Check.

This process authority guides writing before and during the change. `project-memory-skill` records sanitized, verified outcomes only after independent Ending PASS. Neither substitutes for the other.

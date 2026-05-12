---
name: qin-unity-csharp-minimal-style
description: Primary global Unity C# skill for this user's projects. Use for Unity C# tasks across projects whenever Codex creates, edits, refactors, formats, reviews, debugs, explains, or optimizes MonoBehaviours, ScriptableObjects, managers, gameplay systems, or other runtime C# code. This is the shared default Unity C# style unless a tighter repo or user instruction overrides it.
---

# Qin Unity C# Minimal Style

Use this skill for Unity C# work across projects. It is the shared default unless a tighter repo or user instruction overrides it.

## Trigger

Use this skill whenever the task involves Unity C# in any way:

- new C# scripts
- edits to existing scripts
- refactors and bug fixes
- formatting or cleanup passes
- performance work inside scripts
- code reviews or explanations of Unity C# code

## Workflow

1. Read this skill before touching any Unity C# script.
2. Read repo-level `AGENTS.md`, local style notes, or direct user instructions next, and treat tighter local instructions as higher priority than this shared skill.
3. Preserve core behavior unless the user explicitly asks for a functional change.
4. For optimize, simplify, or cleanup requests, keep edits inside the current requested code path and do not spread new guard logic, lifecycle changes, data-flow changes, or structure changes across other scripts unless the user explicitly asks for that scope.
5. Apply the required rules below to every Unity C# edit that is not overridden by tighter instructions.

## Required Rules

1. Output format
- Return the final updated C# code first.
- Then briefly explain what changed and why in 1-3 short sentences.

2. `if` statements
- For a single statement, keep the entire `if` on one line without braces.
- Use braces only when the block contains more than one statement.
- Use a plain `if`/`else` for exactly two mutually exclusive outcomes.
- Use `switch`/`case`, a switch expression, or guarded switch cases for three or more outcomes.
- Do not write or keep `if`/`else if` chains for three or more outcomes when C# can express the same behavior with `switch`; for complex predicates, use guarded switch cases with `when`.

3. One-use values
- Inline a value when it is used exactly once and still readable.
- Only create a variable when it is reused or clearly improves readability.

4. Comments
- Give each function or logic block at most one short comment that explains purpose.
- Do not add long paragraph comments or line-by-line commentary.

5. `Awake()` vs `Start()`
- Use `Awake()` for data and component initialization owned by the script, such as `Rigidbody`, `Collider`, `Animator`, and internal fields.
- Use `Start()` for work that depends on other scripts, `ScriptableObject`s, services, or external references.

6. Functions and reuse
- Do not create helper functions that are only used once.
- Inline one-off logic directly where it is used.
- Only create a new function when it is used in multiple places.
- Do not create a new C# script only to simplify a very small or easy structure; keep the logic in the existing script unless the new script removes real complexity or is reused.
- Exception: `Update()` may call one helper used only there when that makes the per-frame flow clearer.

7. `Update()` and allocations
- Do not allocate new objects every frame in `Update()` if they can be reused.
- Store reusable objects on fields and initialize them once, usually in `Awake()`.

8. Fields, locals, and naming
- Default fields to `private`.
- Use underscore names for internal fields and internal locals, such as `_name`, `_currentY`, `_index`, `_offset`, `_damageValue`, `_randomSeed`, and `_enemyHealth`.
- Use clear full-word names instead of abbreviations like `dmg`, `rs`, or `hp`.
- Do not declare public fields by default.
- If something must be exposed, prefer a property with `get; set;`.

9. Function calls and logs
- Keep function calls and log calls on one line.
- Keep spaces after commas.
- Do not fold argument lists across multiple lines unless the user explicitly asks for different formatting.

10. Initialized fields
- If a field or value is initialized in `Awake()` or `Start()`, use it directly.
- Do not add repeated guards like `!= null`, `> 0`, or similar checks around intentionally initialized data.

## Guardrails

- Do not add abstractions, wrappers, or helpers just to make the code look cleaner.
- Do not change multiple authoring, manager, or system scripts just to work around a discovered issue when the user asked only for local optimization; report the issue or ask before broadening scope.
- Do not add defensive checks for impossible states unless the user asks for them or the existing code already depends on them.
- Do not let broader generic formatting advice override this style.

## Examples

- "Rewrite this MonoBehaviour to match our Unity C# style."
- "Refactor this script without changing behavior."
- "Fix the Update allocations and keep the formatting clean."

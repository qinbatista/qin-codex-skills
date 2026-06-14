# Coding Approach

## Think Before Coding

- State assumptions explicitly when they matter.
- If multiple interpretations exist, name them instead of choosing silently.
- If the smallest correct fix turns into a large structural or architectural change, stop and ask with a short plan.
- Define what success looks like before implementing.

## Prefer The Simplest Viable Solution

- Write the minimum code that solves the actual request.
- Do not add unrequested features, abstractions, configurability, fallbacks, compatibility layers, or defensive branches.
- Trust declared inputs, outputs, formats, and contracts. Fix the producer or contract instead of adding consumer-side repair logic.
- For exactly two mutually exclusive outcomes, use a plain `if`/`else`.
- For three or more outcomes, use the language's switch-style construct: Python `match`/`case`, C# `switch`/`case`, switch expressions, or guarded switch cases.

## Keep Edits Surgical

- Touch only what the request requires.
- Match local style unless this skill or a tighter repo instruction says otherwise.
- Remove only unused imports, variables, or helpers made obsolete by your own change.
- Identify the authoritative source path before editing, copying, moving, or generating files.
- Do not mix sibling packages, caches, clones, or workspaces just because filenames look similar.

## Naming

- Use correct English spelling for new identifiers, file names, keys, comments, and prompt labels.
- Keep an existing misspelled name only when required by an external API, persisted schema, third-party contract, or compatibility boundary.
- Use clear full-word names instead of unexplained abbreviations.

---
name: qin-karpathy-guidelines
description: Behavioral coding guardrails to reduce wrong assumptions, overcomplication, and unrelated edits. Use for non-trivial coding, debugging, refactoring, implementation, and review work across languages before making changes so Codex surfaces assumptions, prefers the simplest viable solution, keeps edits surgical, and defines verifiable success criteria.
---

# Qin Karpathy Guidelines

Apply these guidelines before non-trivial code changes. They bias toward caution and clarity over speed, so use judgment on trivial one-line work.

## 1. Think Before Coding

Do not assume silently.

- State assumptions explicitly when they matter.
- If multiple interpretations exist, name them instead of picking one silently.
- If a simpler approach exists, say so.
- If something is unclear enough to risk the wrong change, stop and ask.
- If the smallest correct fix turns into a large structural or architectural change, stop and ask with a short plan before implementing it.

## 2. Simplicity First

Write the minimum code that solves the actual request.

- Do not add features that were not requested.
- Do not add abstractions for one-off logic.
- Do not create a new script, file, module, or utility only to simplify very small or easy structure; keep the logic in the existing file unless the extraction removes real complexity or is reused.
- Do not add configurability that was not requested.
- Do not add error handling for impossible scenarios.
- Prefer fixing the real source-code problem directly instead of layering wrappers, fallback branches, adapters, or sidecar logic on top of bad code.
- For most bug fixes and update requests, change the existing logic at the real source rather than preserving it and adding another layer around it.
- For branching, use a plain `if`/`else` for exactly two mutually exclusive outcomes, and use the language's switch-style construct (`switch`/`case`, Python `match`/`case`, guarded switch cases, or equivalent) for three or more outcomes.
- Do not write or keep `if`/`else if` or `if`/`elif` chains for three or more outcomes when the language supports a switch-style construct; for complex predicates that are not one selector, use guarded switch cases such as Python `match True` with `case _ if ...`.
- If a long solution can be made materially shorter without losing clarity, simplify it.

## 3. Naming And Spelling

Use correct English names in code even when the user request contains typos.

- Do not create new misspelled identifiers, function names, class names, file names, keys, comments, or prompt labels just to mirror a user typo.
- Correct obvious spelling mistakes when naming new code, and use clear English words such as `coordinate` instead of misspellings like `cooridnate`.
- Keep an existing misspelled name only when it is already a required external API, persisted schema field, third-party contract, or compatibility boundary; otherwise rename it to the correct spelling.
- If correcting a requested public name could surprise the user, mention the correction briefly in the response.

## 4. Surgical Changes

Touch only what the request requires.

- Do not "clean up" unrelated code, comments, or formatting.
- Match the local style unless a tighter user instruction says otherwise.
- When the user asks to optimize, simplify, or clean code, only change the current code in the requested scope; do not spread new guard logic, lifecycle changes, data-flow changes, or structure changes across other scripts unless the user explicitly asks for that scope.
- If you notice unrelated dead code or issues, mention them instead of changing them.
- Remove only the unused imports, variables, or helpers made obsolete by your own change.
- Before editing, copying, moving, or generating files, identify the authoritative source path, manifest, or owner for those files. Do not mix sibling packages, caches, clones, or workspaces just because filenames, prompts, or folder names look similar.
- When file content conflicts with its name or manifest entry, trust the actual content and the current source-of-truth folder. Exclude or flag the mismatch instead of silently promoting it.

## 5. Goal-Driven Execution

Turn vague requests into verifiable outcomes.

- Define what success looks like before implementing.
- Prefer a reproduction, test, build, lint, or other concrete check when available.
- For multi-step work, keep a short plan tied to verification.
- When performing a merge, check explicitly for git conflicts and resolve each conflicted file deliberately instead of blindly taking one side.
- When the user already wants rule compliance or cleanup, fix clear violations directly instead of pausing to ask whether to make the obvious update.
- Do not stop at implementation when the task can be verified in the current environment.

# Coding Approach

## Design Decisions After the Writing Gate

`code-writing-philosophy.md` is the mandatory before/during-writing process authority. This reference adds design and UI rules after that gate; it does not duplicate or replace its four process stages.

- State assumptions explicitly when they matter.
- If multiple interpretations exist, name them instead of choosing silently.
- If the smallest correct fix turns into a large structural or architectural change, stop and ask with a short plan.
- Define what success looks like before implementing.

## Mandatory Basic UI Change Gate

For every code change that affects rendered UI, layout, controls, styling, editor chrome, or runtime HUD, apply all six rules before implementation:

1. **Align shared frames:** peer regions that share a template or read as one visual template use the same outer edges, row starts, gutters, and intended height. Unmatched left/right stacks or a tall panel beside a short peer fail unless the asymmetry communicates a clear priority.
2. **Use one row when it fits:** keep related labels, values, inputs, buttons, and compact controls on one line at widths where they fit without overlap, clipping, or unreadable compression. Wrap only at a measured narrow breakpoint; contain long text inside its own bounded area so it does not push neighboring controls down.
3. **Group once:** use one visual boundary for one logical group. Do not add a nested card, panel, fieldset, background, heading, or classification when the parent already supplies that grouping.
4. **Add information on the alignment grid:** put supporting information inside the panel that owns it. If it is a genuinely separate row or category, make the row explicit and align its outer edges and gutters with the surrounding layout; do not append a floating or offset row.
5. **Keep geometry stable:** reserve or contain space for expected loading, status, error, and optional-content states so controls and surrounding panels do not jump or resize unpredictably.
6. **Make state semantics truthful:** visible color, text, icon, badge, and enabled/disabled state must match the real lifecycle or application state.

Accessibility, localization, readable target sizes, and narrow viewports may require wrapping or deliberate asymmetry. Treat each exception as an explicit layout decision, preserve the alignment system after reflow, and send the rendered desktop and narrow states to Ending Real verification.

## User Experience Philosophy

For every UI task or user-facing UI information change, apply both principles:

1. **Respond first, continue safely:** immediately acknowledge a user action in the interface (for example, selected, saved, queued, or working) so the user is never left without feedback. Move non-blocking work to the background when appropriate, then replace the acknowledgement with the real completion, failure, or next-action state. Never present an unfinished operation as complete: the visible label, icon, and control state must truthfully distinguish queued, in-progress, completed, and failed work.
2. **Make information visual first:** prefer the smallest useful visual aid — an icon, emoji, image, status treatment, or diagram — over a dense block of text when it improves comprehension. Keep the essential meaning in accessible text; visuals clarify the message and must not be the only way to understand it.

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

## Automatic spelling correction at naming boundaries

- This rule covers every unambiguous English spelling error, not an allow-list of examples. When a user supplies a misspelled English word or technical name, correct it before creating or changing identifiers, file names, keys, comments, prompt labels, documentation, or user-facing technical labels. For example, normalize `Oraganization` to `Organization`; preserve the requested casing style after correction.
- Use the surrounding domain and established project vocabulary to make a correction. If the spelling could be intentional, proprietary, or plausibly corrected in more than one way, keep the supplied form and ask instead of guessing.
- Treat an existing misspelled name as a rename/migration: search declarations and direct references first, update every internal use to the canonical spelling, and run the smallest compile, import, or direct-reference check that proves the rename is connected.
- At an external API, public, persisted, serialized, or third-party boundary, preserve only the compatibility alias or migration required by that boundary and use the canonical spelling internally. Do not silently rewrite user data or third-party names.
- If a correction was made, finish with a factual mapping such as `Oraganization -> Organization`, identify the affected scope, and state any compatibility handling. Keep that mapping ahead of any requested informal tone so the user can see exactly which name is canonical.

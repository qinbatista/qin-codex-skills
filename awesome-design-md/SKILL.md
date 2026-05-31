---
name: awesome-design-md
description: Use when the user asks for DESIGN.md files, design-md references, brand/UI style documents, Google Stitch-style design system markdown, or wants UI generated in the style of a known product from VoltAgent/awesome-design-md. Provides bundled DESIGN.md references for many brands and developer/product websites.
---

# Awesome DESIGN.md

Use this skill to find and apply bundled DESIGN.md reference files from `VoltAgent/awesome-design-md`.

## Trigger

Use this when the user asks to:

- find or use a `DESIGN.md` file
- copy a brand/style DESIGN.md into a project
- generate, redesign, or review UI in the style of a named product
- compare available DESIGN.md references for a visual direction

## Source

- Repository: `https://github.com/VoltAgent/awesome-design-md`
- Bundled collection: `references/design-md`
- Index and upstream notes: `references/README.md`
- License: `references/LICENSE`

## Workflow

1. Identify the requested brand, product, or visual style.
2. Search the bundled collection first:

   ```powershell
   Get-ChildItem "$HOME\.codex\skills\awesome-design-md\references\design-md" -Directory
   rg -n "brand-or-style-term" "$HOME\.codex\skills\awesome-design-md\references"
   ```

3. Load only the matching `references/design-md/<slug>/DESIGN.md`; do not load the full collection unless the user explicitly asks for a broad comparison.
4. When multiple matches are plausible, choose the closest match by product category and visual direction, then mention the selected slug briefly.
5. Apply the selected DESIGN.md as a design-system reference for UI generation, redesign, or style review.
6. If the user asks to copy a DESIGN.md into a project, copy the selected `DESIGN.md` to the requested destination, usually the project root.

## Selection Guidance

- For developer tools, AI products, docs, dashboards, or SaaS UI, prefer references from similar software products before consumer brands.
- For retail, automotive, fintech, media, or consumer pages, prefer the matching industry category when available.
- For a named product, use the exact matching slug when it exists.
- If the user asks for "like Apple", "like Stripe", "like Linear", or similar, read that product's `DESIGN.md` and use it as the primary style guide.

## Guardrails

- Treat these files as visual reference systems, not exact brand-asset licenses.
- Do not claim the collection is current unless you verify the upstream repository.
- Do not overwrite an existing project `DESIGN.md` unless the user asked for replacement.
- Keep the selected reference path visible in the response so the user knows which style source was used.

## Examples

- "Use a Linear-style DESIGN.md for this dashboard."
- "Copy the Apple DESIGN.md into this project."
- "Find a good developer-tool design reference for this landing page."

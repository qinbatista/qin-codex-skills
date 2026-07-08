# Visual Verification Rubric

Use this reference when `verify-skill` needs to judge whether visible output is acceptable. Visual verification is not one universal taste score. Anchor every verdict to the user's brief, background knowledge, artifact type, and real rendered evidence.

## Table of Contents

- [Core Procedure](#core-procedure)
- [Universal Blockers](#universal-blockers)
- [Web, App, And Product UI](#web-app-and-product-ui)
- [Games And Playable Scenes](#games-and-playable-scenes)
- [Documents, PDFs, Reports, And Slides](#documents-pdfs-reports-and-slides)
- [Images, Artwork, And Generated Visual Assets](#images-artwork-and-generated-visual-assets)
- [Verification Output](#verification-output)

## Core Procedure

1. Read the user's visual context first: audience, domain, output type, target platform, style references, brand constraints, intended mood, accessibility constraints, and what must stay consistent with prior work.
2. Capture real evidence before judging: screenshot, browser viewport, rendered PDF page, slide export, gameplay capture, image output, or supplied reference. Do not accept code-only inspection for a visual claim when rendering is practical.
3. Choose the artifact standard below. Combine standards when the output is mixed, such as a game UI inside a Unity scene or a report dashboard exported to PDF.
4. Compare against any available baseline: previous screenshot, reference image, existing design system, brand guide, golden file, user sample, or prior generated artifact.
5. Return `pass`, `warning`, or `fail`, with the evidence path/state, selected standard, observed issue, and why it matters.

## Universal Blockers

Fail or repair before passing when any of these affect the requested outcome:

- text is clipped, overlapping, unreadable, or too small for the target medium
- controls wrap, collide, drift out of alignment, or lose their hit area
- contrast is insufficient for normal use or required accessibility
- layout breaks at a required viewport, page size, export size, or gameplay camera scale
- the visual style ignores user-provided background, references, brand, or platform context
- decorative media replaces required product, gameplay, document, or data evidence
- the result only looks acceptable in a static crop while the live state, page, animation, or document render fails

## Web, App, And Product UI

Use `ui-problem-index.md` for local recurring problems. Use Taste Skill for landing pages, portfolios, marketing pages, visual redesigns, and similar web surfaces. For dashboards, admin panels, editors, and operational tools, prioritize clarity, density, scanning, state feedback, and task efficiency over cinematic marketing polish.

Check:

- hierarchy makes the primary task or message clear at first glance
- typography uses a coherent scale and stays readable at target breakpoints
- spacing, alignment, radii, color, shadows, and component density form one system
- responsive behavior works at desktop and narrow/mobile widths when relevant
- interactive states, loading, empty, disabled, error, hover, focus, and selected states are present when the user can encounter them
- images and icons support the actual product/task, not generic decoration
- visual decisions preserve the existing app style unless the user requested a redesign

## Games And Playable Scenes

Judge games by gameplay readability and feel, not by static website beauty. A pretty screenshot fails if it hides gameplay information or makes play worse.

Check:

- the player, hazards, goals, interactables, pickups, projectiles, and navigation cues are readable at real gameplay scale
- HUD text, meters, buttons, prompts, and scores do not block action and remain legible during motion
- camera framing shows enough anticipation space and does not crop important actors
- art direction is cohesive across sprites, lighting, particles, UI, menus, and environment
- animation, hit feedback, damage states, transitions, and sound/visual cues communicate cause and effect
- controls and input response feel consistent with the genre and target platform
- performance-sensitive effects do not flood the screen, obscure action, or cause visible stutter
- menus, pause state, fail state, win state, and restart flow are usable if they are part of the requested work

Evidence should include an in-game screenshot or capture from a real play/editor state when practical, not only an asset file viewed alone.

## Documents, PDFs, Reports, And Slides

Judge documents by reading flow, professional polish, and rendered-page usability. A document that parses correctly can still fail visually.

Check:

- title, section hierarchy, captions, tables, charts, and callouts scan in a logical order
- margins, line length, line height, page breaks, headers, footers, and numbering feel intentional
- tables fill the available page area without tiny text, clipped cells, oversized rows, or inconsistent continuation-page scale
- charts have readable axes, labels, legends, units, source notes, and color contrast
- slides have one clear point per slide, readable type from presentation distance, and enough whitespace
- brand elements are consistent but do not overpower the content
- exports/rendered pages match the requested format and do not depend on editor-only appearance

Render representative pages or slides. For long files, sample cover/first page, a dense content page, a table/chart page, and any page most likely to break.

## Images, Artwork, And Generated Visual Assets

Judge image outputs against the prompt, source references, and target use, not only whether they are attractive.

Check:

- subject identity, pose, product shape, style, environment, and requested edits match the brief
- composition has a clear focal point and enough negative space or crop room for the intended use
- lighting, perspective, texture, color, and detail level are internally consistent
- text in the image is correct and legible if text was required; otherwise avoid accidental pseudo-text
- hands, faces, logos, product details, UI screenshots, and repeated patterns do not contain obvious artifacts
- dimensions, transparency, background, safe area, and file format match the deliverable need

Use before/after or reference/output comparison when the task edits or remixes an existing image.

## Data Visualizations And Dashboards

Judge data visuals by truthfulness and decision clarity.

Check:

- chart type matches the comparison, trend, distribution, part-to-whole, map, or relationship being shown
- axes, units, denominators, time windows, and filters are visible or documented
- color encodes real categories or states and is not merely decorative
- labels and legends are readable without crowding or ambiguity
- sorting, scale, baseline, aggregation, and missing-data treatment do not mislead
- dashboard cards support scanning, comparison, and repeated use rather than looking like a marketing page

## Video, Motion, And Animation

Judge motion by whether it improves communication, feedback, or storytelling.

Check:

- motion has a clear purpose: hierarchy, state transition, feedback, continuity, or narrative
- timing, easing, and sequencing feel intentional and do not distract from the task
- captions, subtitles, overlays, and UI remain readable throughout the motion
- cuts, camera movement, and transitions do not hide important information
- reduced-motion or static fallback exists for UI when relevant

## Verdict Rules

- `pass`: real rendered evidence satisfies the user's brief and the artifact-specific standard, with no blockers.
- `warning`: the core goal is met, but a non-blocking uncertainty, optional polish issue, or unavailable secondary check remains.
- `fail`: a blocker prevents the result from satisfying the user's brief, prior behavior, target medium, or artifact-specific standard.

Do not invent precision. If a judgment is subjective, explain the concrete visual reason and tie it to the user's stated background or the selected artifact standard.

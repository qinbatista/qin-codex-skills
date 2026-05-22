---
name: qin-ui-review
description: Cross-project UI review and optimization baseline for browser, app, Unity Editor, and tool surfaces. Use whenever Codex is asked to create, update, optimize, redesign, polish, review, QA, or fix UI/UX for pages, apps, Unity inspectors, custom editor tools, panels, cards, split layouts, dashboards, forms, buttons, typography, labels, visual hierarchy, responsive layout, or user-reported UI problems. Before UI changes, search the UI problem index for related prior issues and apply matching solutions; when a reusable UI correction or rule appears, update the global index in the same turn.
---

# Qin UI Review

Use this as the shared baseline for UI work across projects. If a repo already has a tighter UI skill, search this global problem index first, then let the repo skill add project-specific checks.

## Trigger

- Use for any user-requested UI work: new UI generation, UI updates, UI optimization, `optimize UI`, the common typo `opitmize UI`, redesign, polish, visual review, responsive fixes, and UI bug reports.
- Use for Unity Editor UI too, including custom inspectors, editor windows, ScriptableObject inspectors, dense tool panels, inline buttons, labels, path rows, sliders, and scene/config tooling.
- Use when the request mentions a UI symptom already seen before, such as uneven panels, wrapped labels, weak hierarchy, odd spacing, mismatched typography, unclear copy, or mobile layout issues.
- Use when the user gives a new reusable UI rule. Classify it as global or local first; add only cross-project rules to this skill.
- Use when the user corrects a UI decision during work. Treat that correction as a candidate reusable rule, search the index, and update the index before finishing if the lesson is not already captured.

## Problem Index

- Before doing UI optimization or generation, search `references/ui-problem-index.md` by component, symptom, and requested action.
- If a matching or related problem exists, read only those entries and apply the listed solution before inventing a new approach.
- If no entry matches and the request reveals a reusable cross-project UI issue, add a concise new problem entry with trigger terms, problem, solution, and validation so the same issue is avoided next time.
- Do not add one-off brand taste, product-specific layout choices, or repo-only constraints to the global index; keep those in the closest repo instructions or local skill.
- Treat the index as a UI experience database: first search prior experience, then solve, then capture any genuinely new reusable lesson.
- Do not leave reusable UI feedback only in chat. If the user says to remember, avoid next time, always do this, or explicitly asks to update the UI skill, update the index or this skill before the final response.

## Workflow

1. Classify the UI request as existing-problem lookup, new UI generation, UI update, visual review, or new reusable rule capture.
2. Search `references/ui-problem-index.md` with likely terms before changing UI.
3. For explicit page or screen UI optimization, capture the current rendered page/screen image before implementation and submit that current image to the available ChatGPT/OpenAI image-capable UI optimization workflow.
4. Ask ChatGPT/OpenAI to optimize text, layout, hierarchy, spacing, responsive behavior, interaction clarity, and obvious UI problems while preserving the existing color theme, brand tokens, visual mood, and product style.
5. Use the returned ChatGPT/OpenAI optimized direction as the primary visual target, then apply the matching indexed solution and the core rules below.
6. Capture before/after rendered evidence for page-level optimization when practical, especially full-page desktop evidence plus narrow-width evidence.
7. If the work exposes a reusable new global UI problem, update the index before finishing.
8. Verify the changed UI visually at the relevant breakpoints and report any remaining risk.

## Core Rules

- Hard rule for `optimize UI`, `opitmize UI`, page redesign, page polish, and page-level UI refinement requests: capture the current rendered page/screen image first and submit that current image to the available ChatGPT/OpenAI image-capable UI optimization workflow before implementation.
- The ChatGPT/OpenAI UI prompt must ask for text, layout, visual hierarchy, spacing, responsive behavior, interaction clarity, and obvious UI problem improvements while keeping the same color theme, brand tokens, visual mood, and product style. Do not ask for a new palette unless the user explicitly requests a theme change.
- Use the returned ChatGPT/OpenAI optimized direction as the primary implementation target. Adapt only for accessibility, feasibility, performance, or repo constraints, and keep meaningful deviations explicit.
- Do not skip the ChatGPT/OpenAI current-page-image step for page-level UI optimization. If the image cannot be captured or no image-capable ChatGPT/OpenAI workflow is available, state the concrete blocker before implementation; do not present an ad hoc UI pass as satisfying this rule.
- Do not claim ChatGPT/OpenAI generated UI direction unless saved mockup images, result manifests, screenshots, response text, or equivalent captured evidence exists.
- Same page plus similar function means similar visual treatment.
- Side-by-side panels with similar roles should stay in the same color family and brightness band.
- Do not make one sibling panel much brighter or darker than another unless the contrast signals a real difference in function, priority, or state.
- Large panels or sections should not leave most of their area empty while a small content block sits at one edge.
- If a section is intentionally sparse, rebalance it by centering the content cluster, reducing the container size, or adding relevant supporting imagery.
- Short labels inside pills, chips, tags, and other compact capsules should stay on one line.
- If a compact label wraps, shorten the copy first. Reduce the text size only as a controlled fallback.
- Primary titles, nav labels, and CTA labels should be immediately clear without relying on explanatory add-ons.
- Same-level labels should use the same size band and a similar length budget so one item does not sprawl while its peers stay compact.
- Do not put parenthetical detail inside primary titles, nav labels, or CTA labels. Move the detail into supporting copy if it still matters.
- Responsive UI work needs both a desktop pass and a narrow-screen pass.
- On narrow screens, nav labels, CTA labels, pill labels, and other compact controls should stay single-line. If they do not fit, shorten the label or switch to a folded menu/control pattern before accepting the layout.
- User-facing website copy should describe the user action, choice, or outcome in plain language, not the technical mechanism behind it.
- If a detail is only useful for debugging, implementation, or internal operations, keep it in logs or internal documentation instead of the public UI.
- Do not introduce stray micro-text near major content blocks. Small labels such as eyebrow text, badges, or status words should still feel proportional to the surrounding title and body sizes.
- Use a deliberate type ladder. Titles, headings, eyebrow labels, body text, and captions should come from a small consistent set of size bands instead of random jumps.
- Keep the font-family system tight. One page should not mix three unrelated text fonts or letterform styles without a strong brand reason.
- Same-level text should stay in the same font family or a clearly related family so the page reads as one system, not a collage.
- In split left/right layouts, sibling columns should resolve into a matched panel footprint. If one side stacks multiple panels, the other side should mirror the stack or consolidate into one block with a comparable overall height.
- Same hierarchy should use one consistent type scale and weight system.
- Peer buttons should match height, density, and visual weight unless one is intentionally secondary.
- One viewport should have one dominant focal point.

## Review Pass

1. Compare sibling surfaces first:
   - left/right panels
   - adjacent cards
   - paired form sections
   - dashboard modules in the same task group
2. If the roles are similar, normalize hue family, lightness, saturation, and surface opacity before adding accents.
3. If strong contrast remains, be able to name the reason:
   - different task group
   - primary vs secondary action
   - alert or warning state
   - featured content with higher priority
4. Compare content density to container size. If a panel feels mostly empty, shrink the container, center the content, or add meaningful supporting media.
5. Check compact labels in pills, tags, and small button-like surfaces across the relevant breakpoints. They should read in one line.
6. Compare titles, nav items, and primary actions at the same hierarchy. They should share one size system and a controlled label length range.
7. Run at least one desktop and one narrow-screen visual pass. Treat wrapped mobile nav, CTA, or pill text as a defect to fix, not a note to leave behind.
8. Scan for type-scale outliers. If one small label feels much smaller or one heading feels much larger than its peers without a clear hierarchy reason, normalize it.
9. Scan descriptions, helper text, and supporting copy for technical or internal wording. Rewrite into user language or remove it if the detail is not needed by the user.
10. Scan the page for font-family drift. Headlines, subheads, labels, and body copy should come from one tight family set instead of multiple unrelated fonts.
11. Compare left/right panel rhythm in split layouts. Avoid a dangling extra panel or a visibly shorter stack on one side unless the asymmetry has a clear product reason.
12. Re-check typography and button parity so consistency is not limited to color.

## Guardrails

- Do not use large left/right color contrast as decoration.
- Do not solve weak hierarchy by making one panel very dark and the other washed out.
- Do not leave a large card or panel mostly blank with text stranded in one corner or along one edge.
- Do not add filler images just to occupy space; use relevant product visuals or rebalance the layout.
- Do not let short pill or chip labels wrap to two lines.
- Do not preserve long wording in compact UI just because the original copy was verbose.
- Do not hide details inside parentheses in primary labels.
- Do not let one same-level title or nav item become much longer than its peers when the wording can be compressed.
- Do not accept wrapped mobile nav items, CTA labels, or pill text when a shorter label or folded menu would solve it cleanly.
- Do not expose technical descriptions, implementation details, or internal workflow wording in public website copy.
- Do not use the UI as a place for developer notes, debugging hints, or system-process explanations.
- Do not add tiny decorative text that creates a separate mini-scale for no product reason.
- Do not let headings, labels, and helper text jump between unrelated font sizes inside the same section.
- Do not mix multiple unrelated text fonts on the same page just to create variety.
- Do not let one section switch to a different text family unless the change signals a real, intentional brand or functional role.
- Do not let one side of a split layout carry extra panel blocks while the other side has no matching panel structure.
- Do not leave left/right columns with obviously different total panel height when they are serving parallel roles.
- Reserve big palette jumps for big functional differences.
- When a page feels visually split for no product reason, reduce the contrast rather than adding more styling.

## Output Expectations

- Call out when sibling panels feel unrelated because their brightness or saturation drifts too far apart.
- Call out when a container feels oversized for its content and suggest one concrete fix: shrink it, center the content block, or add a relevant visual.
- Call out when compact labels wrap and suggest the first fix in this order: shorten copy, slightly reduce font size, then adjust width if the component can support it.
- Call out wrapped mobile nav or CTA text as a blocker and suggest the smallest clean fix: shorten the label, fold the menu, or change the control pattern.
- Call out when same-level labels drift in size or length and suggest one rewrite that removes detail and keeps the wording parallel.
- Call out when a small label feels undersized next to a headline and suggest a size normalization instead of adding another special-case style.
- Call out when split columns have unmatched panel counts or total heights and suggest one concrete resolution: mirror the stack, merge into one panel, or rebalance the heights.
- Call out when copy sounds technical or internal and suggest a user-facing rewrite; if the detail is only useful operationally, move it to logs or internal notes.
- Call out when a page mixes too many text families and suggest collapsing back to one primary family plus, at most, one clearly justified accent family.
- For page-level UI optimization, report the current-page image submitted to ChatGPT/OpenAI, the optimized direction or mockup evidence received, and the final full-page rendered preview.
- Prefer concise wording such as: "These panels serve the same job, so bring them into the same brightness band."
- When contrast is justified, state the product reason instead of describing it as personal taste.

## Examples

- "Make this dashboard UI better" means search the index for dashboard, panels, density, hierarchy, typography, buttons, and responsive issues before editing.
- "The mobile buttons look broken" means search for mobile, button, CTA, wrap, height, and compact label issues before deciding the fix.
- "Do not let tiny labels appear next to big headers again" means add or update a global index entry if the rule is not already covered.

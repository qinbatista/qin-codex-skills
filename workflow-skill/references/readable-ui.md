# Readable UI and visual presentation

Apply these shared preferences to every UI or visual presentation task: websites, dashboards, tools, PDF reports, documents, and slide presentations. They apply even when no code changes and another Skill owns the renderer or export. Read relevant project memory first; missing memory skips. Keep project-specific content and style with its project. Skill-governed design retains the user's selected model and effort.

## Twelve basic principles

1. **Preserve horizontal headers.** Keep header items together in one contained row on desktop and smaller screens. Reclaim unnecessary gaps and padding first; use concise labels or compact navigation when needed. Do not stack header items, overflow the container, or shrink text until it becomes unreadable.
2. **Group simply.** One visual boundary represents one logical group. Use spacing and alignment before adding nested boxes; do not repeat a grouping already expressed by its parent.
3. **Avoid unnecessary wrapping.** Keep related controls, labels, values, and items in one row whenever they fit readably. Bound long text within its own area so it cannot push neighboring controls away.
4. **Keep labels with their components.** Put button text inside the button and card titles, values, and supporting labels inside their owning card or field group. Avoid detached captions that force readers to match text to an object. Preserve persistent accessible form labels; placeholders alone are not labels.
5. **Simplify functional sections.** Use a clear function name followed by its content. Add only controls and descriptions that support the task; avoid repeated headings, redundant actions, and decorative section chrome.
6. **Align panels and use space efficiently.** Peer regions share outer edges, row starts, gutters, and intended heights. Arrange content to avoid awkward gaps, stranded panels, or large unused areas; do not add empty padding just to manufacture symmetry.
7. **Use fewer rows.** Present the same useful information in less vertical space by combining compatible content and removing redundant rows. Preserve logical reading order and scannability.
8. **Minimize explanatory text.** Prefer clear labels and visible structure. Include descriptions only when needed to understand a decision, limitation, unusual action, or unfamiliar content; do not remove essential context.
9. **Keep desktop and mobile consistent.** Preserve the same hierarchy, meaning, action priority, and interaction logic. Adapt spacing and layout to available width instead of inventing a different product flow.
10. **Contain every element.** Text, controls, media, focus treatment, and data stay inside their intended component, panel, and page bounds. Prevent clipping, overlaps, borders crossed by controls, and accidental page-level horizontal scrolling.
11. **Show more useful information per page.** Tools, platforms, functional websites, and reports prioritize readable information density. Use compact tables, aligned comparisons, and relevant imagery when they help; avoid oversized empty cards or decorative content that pushes useful information away.
12. **Balance typography.** Headings are proportionate to body text and data. Keep body text readable at the intended screen or printed reading size; avoid oversized titles paired with tiny content. Density comes from composition, not shrinking everything.

## Interaction and responsive limits

Reserve or contain loading, status, error, and optional-content space so controls and surrounding layout remain stable. Text, color, icons, badges, and enabled state must reflect the real application state. Immediately acknowledge actions and distinguish queued, in-progress, completed, and failed work. Preserve accessible text, contrast, focus, logical keyboard order, and usable target sizes.

Readability, accessibility, localization, and content meaning take priority over compression. Keep headers in one row through a compact navigation design; elsewhere, reflow at a genuine narrow breakpoint when content cannot fit readably. Preserve alignment and all essential information after reflow. Do not force fit through tiny type, clipping, overlap, or hidden essential content.

## Focused rendered checks

- **Web/UI:** inspect the affected desktop and narrow viewports, including long labels and relevant loading/error states. Check the header remains one contained row, controls remain within their owners, and the page does not overflow. Measure disputed alignment and inspect actual interactions.
- **PDF/documents/slides:** render affected pages or slides at the intended reading size. Inspect balanced type, aligned content, readable tables, useful density, labels within owners, page bounds, and page breaks; avoid orphaned headings or clipped rows. Interaction checks apply only to interactive content.
- Test in the active task with the smallest convincing evidence. A source or wording test cannot establish appearance. Do not start or compile a whole project merely to verify a layout. Ending only saves useful preferences and established outcomes.

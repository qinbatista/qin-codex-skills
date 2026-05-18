# UI Problem Index

Search this file before UI generation, UI updates, UI optimization, or UI review. Use `rg -n "<component>|<symptom>|<action>" references/ui-problem-index.md`, then read only matching entries.

## Entry Format

- `Terms`: search words that should find the problem.
- `Problem`: the UI failure to recognize.
- `Solution`: the default fix to apply.
- `Validation`: the concrete check before finishing.

## Search Map

- `UI-001`: sibling surfaces, cards, panels, same function, inconsistent treatment
- `UI-002`: brightness, saturation, contrast, dark panel, washed out panel
- `UI-003`: empty panel, oversized card, stranded content, sparse container
- `UI-004`: pill, chip, tag, compact label, wraps
- `UI-005`: title, nav, CTA, primary label, parentheses, unclear wording
- `UI-006`: same-level labels, length drift, size drift, peer labels
- `UI-007`: mobile, narrow, responsive, nav wrap, CTA wrap
- `UI-008`: technical copy, internal wording, debug text, implementation detail
- `UI-009`: micro text, eyebrow, badge, tiny label, proportional scale
- `UI-010`: type scale, heading size, font size jumps, random typography
- `UI-011`: font family, mixed fonts, unrelated letterforms
- `UI-012`: split layout, left/right columns, unmatched panel stacks
- `UI-013`: peer buttons, button height, density, visual weight, dropdown refresh icon
- `UI-014`: focal point, competing hero, too many dominant elements
- `UI-015`: decorative contrast, palette jump, unrelated color block
- `UI-016`: filler image, empty visual, irrelevant media
- `UI-017`: no screenshot, no rendered evidence, claimed visual target
- `UI-018`: new UI rule, repeated problem, reusable lesson not captured
- `UI-019`: nested panels, panel inside panel, group inside group, repeated item grouping
- `UI-020`: duplicate action buttons, add beside dropdown, refresh always visible, contextual toolbar
- `UI-021`: slow inspector, slider lag, expensive repaint, refresh during edit, asset scan while dragging
- `UI-022`: read-only path looks editable, file name editable, auto-read assets, inline row actions
- `UI-023`: split label value rows, two-line controls, dense inspector, vertical space waste, layer count grid
- `UI-024`: misplaced delete button, destructive action ownership, add child beside remove, child selector
- `UI-025`: placement simulator, drag preview, missing reference image, parent reference hidden
- `UI-026`: picker cancel, select cancel, unwanted window opens, canceled selection applies
- `UI-027`: same size text boxes, uneven input widths, same row numeric inputs, small count inputs

## Problems

### UI-001 Same-Function Surfaces Look Unrelated

Terms: sibling surfaces, adjacent cards, panels, same function, same role, inconsistent treatment, dashboard modules.
Problem: Elements with the same job use noticeably different color, brightness, spacing, border, opacity, or hierarchy.
Solution: Normalize hue family, lightness, saturation, opacity, border treatment, and spacing before adding accent differences.
Validation: Compare peer surfaces side by side and confirm any remaining difference maps to priority, state, or task group.

### UI-002 Unjustified Brightness Or Saturation Gap

Terms: brightness, saturation, contrast, dark panel, washed out panel, one side brighter, one side darker.
Problem: One sibling panel is much brighter, darker, or more saturated without a real functional reason.
Solution: Bring sibling surfaces into the same brightness band and reserve strong contrast for primary, warning, selected, or featured states.
Validation: State the product reason for any remaining contrast; if none exists, reduce it.

### UI-003 Oversized Empty Container

Terms: empty panel, oversized card, sparse container, stranded content, blank area, content at edge.
Problem: A large card, panel, or section is mostly empty while content sits at one corner or edge.
Solution: Shrink the container, center the content cluster, redistribute layout density, or add relevant supporting media.
Validation: The panel should feel intentionally composed at desktop and narrow widths, not like missing content.

### UI-004 Compact Label Wrap

Terms: pill, chip, tag, badge, compact label, small button, wraps, two lines.
Problem: A short label inside a compact capsule wraps to multiple lines or looks squeezed.
Solution: Shorten the copy first, reduce font size only as a controlled fallback, then adjust width if the component pattern supports it.
Validation: Compact labels remain one line across the target breakpoints.

### UI-005 Primary Label Carries Too Much Detail

Terms: title, nav, CTA, button label, primary label, parentheses, unclear wording, verbose label.
Problem: Titles, nav labels, or CTA labels use long wording, parentheses, or technical qualifiers that slow scanning.
Solution: Keep the primary label short and plain; move detail into supporting copy only when users need it.
Validation: Same-level primary labels are immediately clear without parenthetical explanation.

### UI-006 Same-Level Label Drift

Terms: same-level labels, peer labels, length drift, size drift, parallel wording, nav item.
Problem: One label in a peer group is much longer, larger, heavier, or more detailed than the others.
Solution: Rewrite labels into parallel length and meaning, then align type size and weight within one hierarchy band.
Validation: Peer labels scan as one system and none dominates by accidental length or weight.

### UI-007 Mobile Compact Control Failure

Terms: mobile, narrow, responsive, nav wrap, CTA wrap, button wrap, pill wrap, folded menu.
Problem: Mobile nav, CTA, pill, or compact control text wraps, overlaps, clips, or forces awkward layout width.
Solution: Shorten labels, switch to a folded menu/control pattern, or change the component layout before accepting the design.
Validation: Check at least one narrow viewport; compact controls stay readable, single-line where expected, and non-overlapping.

### UI-008 Technical Or Internal Public Copy

Terms: technical copy, internal wording, debug text, implementation detail, workflow text, system process.
Problem: Public UI text describes implementation mechanics, debugging, internal process, or system behavior instead of user action or outcome.
Solution: Rewrite in user-facing language or remove it from the UI if it belongs in logs, docs, or developer tooling.
Validation: A target user can understand the copy without knowing the implementation.

### UI-009 Stray Micro Text

Terms: micro text, eyebrow, badge, tiny label, undersized label, proportional scale.
Problem: Small decorative text appears near major content at a size that feels disconnected from the surrounding type scale.
Solution: Normalize the label into the page type ladder, enlarge or remove it, or make it a real metadata/status element.
Validation: Eyebrows, badges, captions, and status labels feel proportional to nearby headings and body text.

### UI-010 Random Type Scale

Terms: type scale, heading size, font size jumps, random typography, type ladder.
Problem: Headings, labels, helper text, and captions jump between unrelated sizes or weights.
Solution: Use a small type ladder for titles, headings, labels, body, and captions; normalize outliers.
Validation: Same hierarchy uses the same size and weight band across the screen.

### UI-011 Font Family Drift

Terms: font family, mixed fonts, unrelated fonts, letterforms, typography drift.
Problem: One page mixes unrelated text fonts or switches font families without a brand or functional reason.
Solution: Collapse to one primary family plus at most one clearly justified accent family.
Validation: Headings, labels, and body text read as one typographic system.

### UI-012 Unbalanced Split Layout

Terms: split layout, left column, right column, side by side, unmatched stack, panel count, column height.
Problem: Parallel left/right columns have unmatched panel counts, visibly different total heights, or a dangling extra block with no reason.
Solution: Mirror the stack, merge related panels, rebalance heights, or change to a layout that does not imply parallel roles.
Validation: The split layout has a matched footprint unless asymmetry communicates a clear product priority.

### UI-013 Peer Button Mismatch

Terms: peer buttons, button height, button density, visual weight, action row, primary secondary, field action height, inline action buttons, dropdown refresh icon.
Problem: Buttons in the same action group, or inline buttons beside a field, have inconsistent height, padding, density, icon scale, or baseline without intentional hierarchy.
Solution: Normalize height, padding, icon size, and baseline; make primary vs secondary differences deliberate and restrained. For field plus inline action rows, draw or constrain the field and buttons to the same row rect height. When inline actions belong to a row that also has a right-side preview/image column, reserve the same right column width for the main action group so buttons, inputs, and preview edges align; keep compact delete/remove controls beside the item identity instead of stealing width from paired actions. For selector rows with contextual refresh/sync icons, do not rely on Unity default popup/button visual heights; set explicit popup and button styles so both draw from the same row height.
Validation: Peer buttons align cleanly, inline field actions share the same height as their field, selector plus refresh rows have matching visual height, row action groups align to the preview/image column, compact delete/remove controls do not squeeze paired actions, and only the intended primary action has extra emphasis.

### UI-014 Too Many Dominant Focal Points

Terms: focal point, competing hero, dominant element, visual priority, attention split.
Problem: Multiple large, bright, or heavy elements compete for primary attention in one viewport.
Solution: Pick one dominant focal point and demote the others through size, contrast, placement, or grouping.
Validation: A first glance reveals one main action, status, or content area.

### UI-015 Decorative Contrast Without Function

Terms: decorative contrast, palette jump, unrelated color block, color contrast, split page.
Problem: Large color or palette shifts are used as decoration and make related sections feel like unrelated products.
Solution: Reduce decorative contrast, keep related areas in one palette system, and reserve strong palette changes for state or function.
Validation: Any palette jump can be explained by task group, status, warning, selection, or priority.

### UI-016 Filler Image Or Empty Visual Slot

Terms: filler image, irrelevant media, empty visual, decorative image, placeholder.
Problem: An image or visual is added only to fill space and does not clarify the product, object, task, or state.
Solution: Use relevant product/state media, a real generated visual, or rebalance the layout so no filler is needed.
Validation: The visual has a clear job beyond decoration.

### UI-017 Missing Rendered Evidence

Terms: no screenshot, rendered evidence, visual target, mockup, before after, screenshot step.
Problem: UI optimization is implemented or claimed from intuition only, without current rendered evidence or a saved visual target when one was needed.
Solution: Capture the current UI, use the available image UI optimization workflow for page-level polish when practical, and keep before/after evidence.
Validation: The final report or response can point to screenshots, mockups, manifests, or a clear blocker if evidence capture was unavailable.

### UI-018 New Reusable UI Rule Not Captured

Terms: new UI rule, repeated problem, reusable lesson, don't happen again, add rule, user preference.
Problem: The user gives a cross-project UI correction, but the lesson remains only in the chat and the same issue can recur.
Solution: Classify scope first. If global, add or update one concise entry in this index; if local, update the closest repo skill or AGENTS.md.
Validation: The new rule is searchable by symptom and includes trigger terms, solution, and a concrete check.

### UI-019 Nested Panel Grouping Confusion

Terms: nested panels, panel inside panel, group inside group, card inside card, repeated item grouping, item list, data group.
Problem: A repeated item list uses an outer container plus additional boxed subcontainers inside each item, making it unclear which border defines the real logical group.
Solution: Use one bordered panel per logical item or data group. Keep repeated item siblings visually separated, but render fields, values, child rows, and previews inside that item without additional nested panel borders unless they are truly separate objects.
Validation: In the rendered UI, a user can identify each logical item from one outer border, and no item has unnecessary inner boxed groups competing with that border.

### UI-020 Non-Contextual Toolbar Clutter

Terms: duplicate action buttons, create refresh buttons, add button beside dropdown, plus beside selector, refresh always visible, dirty refresh, contextual toolbar.
Problem: A toolbar shows multiple overlapping actions, separate add/delete buttons beside a selector, or refresh controls even when there is nothing to refresh.
Solution: Keep one primary action for the main workflow. Put add/new as an explicit option inside the selector when the selector owns the chosen item. Do not repeat a section label beside a self-explanatory selector when the selected value already names the context. Show refresh/sync as a compact icon next to the selected name only when a real dirty/out-of-sync state exists. Remove destructive delete buttons from the header unless deletion is the primary expected workflow.
Validation: The rendered toolbar has one main action, add is discoverable from the selector, the selector row does not waste space on redundant labels, refresh is hidden when clean and visible when dirty, and destructive controls do not compete with normal creation flow.

### UI-021 Expensive Work During Value Editing

Terms: slow inspector, slider lag, expensive repaint, refresh during edit, asset scan while dragging, preview load while dragging, value edit should only save config.
Problem: A value control triggers asset scans, preview generation, refresh, creation, or other expensive sync work during drag/repaint, making basic editing feel slow and unpredictable.
Solution: Treat value edits as local config edits only. Cache previews and expensive dirty checks. Run folder scans, asset sync, generation, or refresh only from explicit add/refresh/create actions or external asset-change invalidation.
Validation: Dragging sliders or editing numeric values does not call folder scans, preview generation, or asset creation paths, and the UI remains responsive while serialized config values update.

### UI-022 Read-Only Imported Paths Look Editable

Terms: read-only path looks editable, imported file path, file name editable, auto-read assets, folder-read assets, inline row actions, actions on new line, save vertical space.
Problem: Auto-populated asset paths or filenames use editable input styling, or row actions sit on a separate line, implying users should manually edit imported identity fields and wasting vertical space.
Solution: Render auto-read identity/path values as passive read-only labels or boxes, not text fields. Put row-local actions such as add child and remove directly on the same row after the value when space allows.
Validation: Users can tell the path/name is not editable, and each row uses one line for the value plus row actions without avoidable vertical stacking.

### UI-023 Split Label/Value Rows Waste Space

Terms: split label value rows, labels above values, two-line controls, dense inspector, compact editor, vertical space waste, same line labels, layer count grid, count fields.
Problem: Dense editor or tool UI shows simple labels on one row and their adjacent values on a second row even though each label only identifies one nearby input.
Solution: Put each short label and its value/input in the same row when the pair is compact and directly related. Put compact coordinates or per-item metadata directly after the item name/path when it edits that same item, instead of creating a separate full-width row. For small numeric counts, keep each label beside a short equal-width field in one row instead of stretching the inputs into oversized columns or wrapping into two rows. Keep separate rows only for complex controls, long labels, or layouts where one-line pairing would harm readability.
Validation: Compact value groups use one row per logical group, item-level coordinates/metadata sit beside the item identity when space allows, labels stay readable, and vertical scrolling is reduced without hiding the relationship between label and input.

### UI-024 Destructive Action Ownership Is Unclear

Terms: misplaced delete button, destructive action ownership, add child beside remove, child delete, parent delete, remove button, child selector, multi image child.
Problem: A remove/delete button sits next to an unrelated add/select action, making users think it removes the wrong object. Child rows also fail when they can be created without choosing their actual image.
Solution: Place destructive actions inside the object they delete, away from unrelated creation controls. Put parent removal at the parent item's bottom or clear item action area; put child removal inside each child row/panel. Make child creation/select controls choose real assets, and support multi-add through selected assets when the workflow naturally allows it.
Validation: A user can identify whether an action affects the parent or child before clicking, no empty unusable child item is created, and multi-selected child assets can be added without repeated single-image steps.

### UI-025 Placement Tools Need A Visible Reference Image

Terms: placement simulator, drag preview, image reference, missing reference, parent reference hidden, child position editor, visual placement, duplicate preview.
Problem: A drag-based placement tool hides the fixed reference, duplicates preview images outside the actual workspace, or writes serialized/config data continuously while dragging.
Solution: Use one main placement canvas with the fixed parent/reference image centered and labeled, then draw the draggable child/object on top with a clear outline. Map screen dragging from the fixed parent pivot/origin to the serialized local position instead of auto-fitting the child as part of the view bounds. Avoid duplicate preview panels unless they solve a real ambiguity, and persist config changes on release/commit instead of every drag frame.
Validation: A user can identify the parent reference, draggable child/object, fixed pivot/origin, and current position in one canvas, and dragging remains responsive without continuous asset/config writes.

### UI-026 Canceling Pickers Must Be A No-Op

Terms: picker cancel, file dialog cancel, select cancel, unwanted window opens, canceled selection still applies, accidental modal.
Problem: A select/import button opens a picker, but canceling the picker still triggers follow-up work such as opening another window, applying old values, or running an action.
Solution: Treat cancel as a hard no-op. Gate all follow-up UI, data mutation, imports, and secondary windows on a newly selected valid result. Keep separate actions separate, such as `Select` only selecting and `Place` only opening placement.
Validation: Canceling a picker leaves fields, windows, generated files, and selection state unchanged.

### UI-027 Peer Text Fields Need Equal Input Width

Terms: same size text boxes, uneven input widths, peer text fields, label steals field width, dense inspector fields, same row numeric inputs, small count inputs, right edge gap, unused row width.
Problem: Peer inputs in the same logical group share the same row or grid, but longer labels reduce only their own input width, or fixed tiny fields leave a large dead gap at the right edge.
Solution: Reserve label widths consistently for the peer group, then compute equal input widths from the remaining row space. For small numeric count fields, keep them compact only when the row still reaches the intended edge; if a visible dead gap remains, distribute the surplus into equal wider fields instead of leaving unused space.
Validation: Same-level text boxes line up visually, have matching width across the group, fill the intended row width without overflow, and keep labels readable.

### UI-028 UI Updates Need A Visual Target First

Terms: UI update, make UI better, ugly UI, Unity inspector, editor UI, visual reference, image reference, repeated retries, ChatGPT image review.
Problem: UI changes are implemented directly from code guesses, causing repeated mismatched layouts, clipped text, and user-visible trial and error.
Solution: Capture the current rendered UI first, use ChatGPT/OpenAI image understanding or the available image UI optimization workflow to define a visual target, then implement against that reference. For dense Unity inspector tools, separate overloaded concerns into matching rows or groups instead of forcing every control into one line.
Validation: Before coding, there is a screenshot or clear visual target; after coding, the rendered UI is checked against it for alignment, matching control sizes, readable labels, and no clipping.

# Report Manifest

Use this JSON shape for `scripts/generate_test_pdf_report.py`.

## Contents

- [Required top-level fields](#required-top-level-fields)
- [`purpose`](#purpose)
- [`request_summary`](#request_summary)
- [`overview`](#overview)
- [`environment`](#environment)
- [`artifacts`](#artifacts)
- [`layout_style`](#layout_style)
- [`test_cases`](#test_cases)
- [Evidence contract](#evidence-contract)
- [Compactness and layout behavior](#compactness-and-layout-behavior)

## Required top-level fields

```json
{
  "title": "MuseAI Smoke Test Report",
  "subtitle": "Local web flow verification",
  "generated_at": "2026-04-21T14:30:00-07:00",
  "purpose": {
    "category": "ui",
    "label": "UI Validation",
    "focus": [
      "desktop layout",
      "mobile CTA"
    ]
  },
  "request_summary": {
    "requested_change": "User asked to verify the homepage CTA layout after edits.",
    "expected_outcome": "CTA stays on one line on desktop and remains readable on narrow screens."
  },
  "summary": "Short top-line summary.",
  "overview": {
    "status": "warning",
    "passed": 5,
    "failed": 1,
    "warnings": 2,
    "skipped": 0
  },
  "environment": {
    "workspace": "/path/to/workspace",
    "target": "http://localhost:3000",
    "branch": "main"
  },
  "comparison_mode": false,
  "layout_style": "default_compact",
  "artifacts": [],
  "test_cases": []
}
```

## `purpose`

Use `purpose` to classify what the report is mainly for so the report can emphasize the right kind of evidence.

```json
{
  "category": "image",
  "label": "Image Edit Review",
  "focus": [
    "before and after comparison",
    "visual defects",
    "before data",
    "after data"
  ],
  "audience": "User review"
}
```

Recommended categories:

- `code`
- `ui`
- `image`
- `api`
- `document`
- `mixed`

## `request_summary`

Use this when the user asked for a concrete edit, fix, or expected result and you want that target visible near the top of the report.

```json
{
  "requested_change": "User asked to fix the login button overlap.",
  "expected_outcome": "Buttons should align and keep equal height.",
  "scope": "Desktop and mobile login page"
}
```

## `overview`

- `status`: `pass`, `failed`, `warning`, `skipped`, or `info`
- count fields are optional, but include them when known

## `environment`

May be either:

- a JSON object
- or a list of label/value rows

Examples:

```json
{"workspace": "/repo", "target": "http://localhost:3000"}
```

```json
[["Workspace", "/repo"], ["Target", "http://localhost:3000"]]
```

## `artifacts`

Top-level artifacts appear before the test case details. Use them for screenshots, overview images, dashboards, or other high-value visuals.
Tall top-level evidence images are rendered as full-width readable slices so a long screenshot or preview does not become a tiny thumbnail with large empty page space.

```json
[
  {
    "label": "Desktop screenshot",
    "path": "/absolute/path/desktop.png",
    "caption": "Home page after login",
    "fit_mode": "contain",
    "preserve_full_image": true
  }
]
```

Use `fit_mode: "contain"` or `preserve_full_image: true` for product, garment, generated asset, before/after, and document-page evidence where the complete object must remain visible on one page. Leave these fields unset for long screenshots or log images that should be split into readable continuation slices.

## `layout_style`

Use `layout_style` as a planning hint for the report shape. It does not mean every report must use the same renderer.

Recommended values:

- `default_compact`: ordinary code, API, command, or short UI checks
- `step_by_step`: process reports where the reader needs instructions, ordered actions, and expected/actual results
- `before_after_review`: edit reviews, baseline/current checks, regressions, and visual diffs
- `side_by_side_comparison`: reports where two or more outputs must be compared against the same source, baseline, or target
- `image_gallery_review`: screenshot-heavy or image-heavy review evidence
- `audit_review`: document, prompt, configuration, or structured-data audits
- `custom`: user supplied or case-specific format that does not fit the generic renderer cleanly

When `layout_style` is not `default_compact`, choose the page structure that best shows the evidence. Use the generic generator only when it can express the selected layout clearly; otherwise build a custom PDF from the same manifest/evidence and keep the usual cache and verification rules.

Optional page planning fields:

```json
{
  "orientation": "landscape",
  "page_fit_strategy": "keep each visual case, legend, and table together on one page when practical",
  "reader_instructions": [
    "Use the colored headers to identify each compared side.",
    "Compare the visual evidence first, then confirm details in the table."
  ]
}
```

## `test_cases`

Each test case can include:

```json
{
  "name": "Login flow",
  "status": "pass",
  "function_name": "AuthClient.login()",
  "input_label": "Input",
  "output_label": "Output",
  "input": "Open login page and submit valid credentials.",
  "input_image_path": "/absolute/path/login-form.png",
  "used": "Playwright opened http://localhost:3000/login and submitted the form.",
  "output": "Redirected to dashboard.",
  "pass_reason": "The final URL was /dashboard and the dashboard heading was visible, matching the expected logged-in state.",
  "show_details": false,
  "summary": "Login flow succeeded end to end.",
  "request": "POST /api/login {\"email\":\"demo@example.com\",\"password\":\"••••••••\"}",
  "response": "302 /dashboard",
  "objective": "Confirm the user can sign in.",
  "result": "Login succeeded and redirected to dashboard.",
  "steps": [
    "Open login page",
    "Submit valid credentials",
    "Wait for dashboard URL"
  ],
  "details": {
    "final_url": "/dashboard",
    "duration": "4.2s"
  },
  "notes": [
    "No console errors",
    "Layout remained stable on desktop"
  ],
  "artifacts": [
    {
      "label": "Dashboard screenshot",
      "path": "/absolute/path/dashboard.png",
      "caption": "Post-login state"
    }
  ]
}
```

## Evidence contract

Every passing case must include concrete evidence rows, not only a status:

- `input`: the real file, image, URL, payload, command input, code path/snippet, prompt, request, or generated test data
- `used`: the exact tool, command, script, browser action, API endpoint, model call, or workflow used
- `output`: the real stdout, JSON, return value, screenshot path, rendered artifact, generated file, page state, response, or diff
- `pass_reason`: why that specific output satisfies the user's requested outcome

Use aliases only when a legacy manifest already has them: `request` can stand in for `input`, `response` can stand in for `output`, and `why_passed`, `why_pass`, or `acceptance_reason` can stand in for `pass_reason`.

Evidence must match the artifact type:

- Image evidence: include the source/output image path and, when useful, add it in `artifacts`.
- Link/URL evidence: include the exact URL plus HTTP response, final URL, page state, or extracted content.
- Code evidence: include the code path or snippet, the command that ran it, and the returned value/log.
- Result evidence: include the actual value, file, JSON, stdout, screenshot, or generated artifact.

Do not write a pass case whose output is only `OK`, `PASS`, `done`, `works`, or another bare status word.

The bundled PDF generator rejects passing cases that are missing `input`, `used`, `output`, or `pass_reason`, and rejects passing cases whose `output` is only a bare status word.

Top-level compactness control:

```json
{
  "case_detail_mode": "compact"
}
```

Preferred case rows:

- `request`: raw API request or real request example when available
- `response`: raw API response or real returned text when available
- `input`: real given text, command, payload, prompt, or executed action
- `input_image_path`: optional real source image to render inside the `Input` row when the case input includes an image
- `used`: exact command, script, tool, browser route, API endpoint, model call, or workflow used to produce the output
- `output`: real returned text, log excerpt, or concrete result
- `pass_reason`: required for passing cases; explain why the observed output satisfies the expected outcome
- for model names, prompts, system prompts, request payloads, or other long setup text requested by the user, add a clearly named test case near the top, such as `Models and prompt used`, with the model names in `input`, the full prompt in `output`, and a readable prompt-card image in `artifacts` when practical
- `function_name`: optional short function or API entry-point name to show in the title row
- `case_detail_mode`: optional top-level manifest setting. Default is `compact`. Use `full` only when the user explicitly wants all supporting detail rows shown.
- `show_details`: optional per-case override that forces one case to show its support rows even when the manifest stays compact
- `summary`: optional short explanation after the concrete example rows
- `input_label`: optional display label for the `input` row. Default is `Input` when a real example is present, otherwise `Check`.
- `output_label`: optional display label for the `output` row. Default is `Output` when a real example is present, otherwise `Result`.
- `objective` and `result` remain supported as fallback summary inputs for older manifests, but new manifests should prefer `request` / `response` or concrete `input` / `output`
- keep `details` for compact structured values such as `command`, `tests_ran`, `final_url`, `duration`, or compare-style fields
- keep `notes` only for short supporting facts that do not fit `input`, `output`, or `details`
- keep `artifacts` for real evidence images; `images` is also accepted as an alias
- use `comparison_mode: true` at the manifest or case level when the report is a baseline/current, before/after, regression, or visual-diff comparison
- for comparison cases, provide `before`, `after`, `before_image_path`, and `after_image_path` directly on the case or inside a `comparison` object
- comparison cases render `Before` and `After` rows before any `Comparison` or `Final Result` row, so do not put only the final output in `output`
- render each case as one table:
  - first row: bold case title with inline status, such as `Verification 1: Login flow | PASS`
  - if `function_name` is present, prefer it in the title row so the user immediately sees which function or API path is being shown
  - following rows: `Label | Value`, with concrete example rows first, usually `Input | ...`, `Used | ...`, `Output | ...`, and `Why Pass | ...`
  - default compact mode should usually stop there
  - only add `Summary`, `Scenario`, metrics, or `Notes` rows when the user explicitly wants detailed mode or one specific case needs extra explanation
  - merge repeated notes into one `Notes` row when detailed mode is enabled

Comparison case example:

```json
{
  "name": "Flat sketch generation comparison",
  "status": "pass",
  "comparison_mode": true,
  "comparison": {
    "before": "Baseline output used one final front sketch only.",
    "after": "Updated output includes front and back sketches with matching measurement callouts.",
    "before_image_path": "/absolute/path/before.png",
    "after_image_path": "/absolute/path/after.png",
    "summary": "The after image preserves the garment silhouette and adds the missing back view."
  },
  "output": "Accepted after visual review."
}
```

Side-by-side comparison example:

```json
{
  "title": "Comparison Report",
  "comparison_mode": true,
  "layout_style": "side_by_side_comparison",
  "orientation": "landscape",
  "reader_instructions": [
    "Both panels use the same source image; compare the overlays and table values.",
    "The left and right header colors identify which result belongs to each side."
  ],
  "source": {
    "label": "Source image",
    "path": "/absolute/path/source.png"
  },
  "sides": [
    {
      "side": "left",
      "label": "Baseline",
      "color": "#1D4ED8"
    },
    {
      "side": "right",
      "label": "Current",
      "color": "#047857"
    }
  ],
  "cases": [
    {
      "name": "Case 1",
      "left_image_path": "/absolute/path/left.png",
      "right_image_path": "/absolute/path/right.png",
      "table_rows": [["Metric", "Left", "Right"], ["Detected item count", "6", "6"]]
    }
  ]
}
```

For `side_by_side_comparison`, prefer this page order:

- Page 1: compact title, goal/result summary, reader instructions, setup details needed to interpret the evidence
- Case pages: side-by-side panels in the requested order, clear labels/colors, short legend, and the supporting table kept on the same page when practical
- If a side panel is labeled as one side's result, draw only that side's annotations in the panel. Put reference, expected, or baseline values in a separate table or a separately labeled combined-overlay panel.
- Optional final page: aggregate metrics, failures, warnings, or conclusions only when they add value

Step-by-step report example:

```json
{
  "title": "Workflow Validation Report",
  "layout_style": "step_by_step",
  "orientation": "portrait",
  "reader_instructions": [
    "Follow the steps in order.",
    "Each step shows action, expected result, actual result, and evidence."
  ],
  "steps": [
    {
      "step": "Open target page",
      "expected": "Page loads without console errors.",
      "actual": "Loaded successfully.",
      "evidence_path": "/absolute/path/step_01.png"
    }
  ]
}
```

For `step_by_step`, prefer one step block per page or one compact group of short steps per page. Keep each step's action, expected result, actual result, and evidence together unless the evidence is too large.

## Formatting guidance

- Keep `summary`, `objective`, and `result` short.
- Keep `request_summary` short and tied to the user's real ask.
- Prefer screenshots and tables over long prose.
- Prefer real request, response, prompt, command, log, and result text over summary-only wording.
- Every passing case needs real `Input`, `Used`, `Output`, and `Why Pass` rows.
- Choose the report format from the case type instead of forcing every PDF into the default compact test-case table.
- For comparison reports, show the real before data and after data plus before and after images when available. Do not produce a final-only case.
- For side-by-side comparison reports, make each side visually identifiable and keep the comparison instruction, evidence panels, and supporting table together on the same page when practical.
- For step-by-step reports, make the instructions and ordered steps visible before the evidence detail.
- Keep report section titles explicit, usually `Summary`, `Verification Summary`, `Verification N`, and `Evidence`.
- Add one short legend near the testing section so the user knows that `Input` is what was given, `Used` is what ran, `Output` is what came back, and `Why Pass` is the acceptance reason. `Check` / `Result` should stay fallback summary labels only for non-pass or legacy cases.
- Size tables adaptively from content and the page, not from fixed tiny defaults. Estimate the row count, wrapped text length, column count, and available page rectangle before choosing the page size, orientation, font size, row height, and continuation splits.
- Maximize useful page use: short comparison tables should become larger and easier to read, with bigger type and row height; dense comparison tables should become smaller only as needed to remain readable.
- Avoid report pages where the table uses only the top strip and leaves most of the page blank. If a table is short, enlarge it or merge it with nearby evidence; if it is wide, use landscape or a larger page before shrinking text.
- Avoid inconsistent table scale between pages unless the data density genuinely differs. Recompute density per logical table group, and keep same-group pages visually consistent.
- Split tables by semantic groups, row chunks, or column groups only when a single page would be unreadable. Do not create several sparse pages for one small table.
- After rendering, inspect page PNGs for tiny text, excessive blank space, clipped cells, awkward page breaks, and unusable column widths. Regenerate with adjusted sizing before delivering.
- Keep the report header visually proportional. Avoid oversized title and subtitle blocks when a smaller, tighter title fits the page better.
- Prefer one compact first-line meta banner for purpose, status, and counts instead of multiple full-width banner rows.
- Keep the first page summary short, usually `Goal`, `Result`, and `Context`, instead of splitting basic metadata across many small tables.
- Keep label/value column widths consistent between the top summary table and the per-case tables so the report reads as one system.
- Keep the first label column compact across those tables so short labels do not waste page width.
- If a summary section only needs a status marker, prefer a full-width row with inline status instead of introducing a separate narrow status column that breaks the report rhythm.
- Put the case title and status together in the first row instead of adding a separate `Status:` text row.
- Default each test case to a two-column label/value table with concrete example rows first.
- Prefer `Input` / `Output` for function and API examples unless a more specific label is truly clearer.
- Keep the first five case rows easy to scan: title row, `Input`, `Used`, `Output`, then `Why Pass`.
- Keep compact mode as the default. In normal reports, do not print `Summary`, `Scenario`, `Response Length`, `Input Image Size`, or `Notes` for every case.
- Use a short `Summary` row only when the concrete example rows still need one line of interpretation or when the manifest explicitly enables detailed mode.
- Vertically center table cells so short labels stay visually aligned against taller wrapped value cells.
- Center the top meta-banner text line inside the banner instead of leaving it left-aligned within a wide dark bar.
- If you use 2 or 3 columns, keep the first column as the label and keep the remaining columns limited to short status or value fields.
- Avoid wide freeform `Result` prose columns that create large blank gaps.
- Bias toward fewer rows so the user can understand the result quickly.
- Keep each table row to one fact whenever possible.
- Use absolute file paths for image artifacts when possible.
- Keep missing artifacts in the manifest so the PDF can show what was expected.
- Keep missing before or after comparison evidence in the manifest too. The PDF should show that the comparison evidence was missing instead of hiding the row.
- For code and API reports, include screenshot-style evidence images for important command output, log excerpts, or payloads when available.
- Keep those evidence images aligned to the same main content width as the report tables, and prefer case-level evidence placement over a generic top-level evidence block when the image belongs to one specific test.
- If you generate a function example image from the case data, keep its visible card width aligned to the report tables and keep the image sections in the same order as the case rows: function, input, output.
- If the case input includes a real source image, prefer rendering that image as a compact thumbnail directly inside the case table's `Input` row instead of keeping a separate large image artifact.
- Wrap long output text inside its panel and increase the panel height when needed so the text never spills past the card boundary.
- Keep captions under those example images very short, and omit them completely when they only repeat what the image title or the table above already says.
- After generating the PDF, render representative pages and check the real page images. If a section breaks awkwardly across pages, adjust orientation, scaling, table density, or page grouping and regenerate.
- Use landscape pages for wide comparisons, screenshot grids, or wide tables. Use portrait pages for text-heavy steps, document reviews, and long vertical screenshots.
- For image and UI reports, use richer visual artifacts.
- For code and API reports, include compact details and metrics tables even when screenshots are limited.

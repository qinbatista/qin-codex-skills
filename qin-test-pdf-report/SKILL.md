---
name: qin-test-pdf-report
description: Generate a visual PDF report for testing, QA, validation, verification, checks, regressions, audits, review evidence, and reviewable result reporting. Use when the user asks for testing, asks to see a PDF report, wants a visual report, wants a report artifact, wants QA or validation evidence, wants proof with screenshots or tables, or when a project requires result reporting in a clearer form than plain text. Prefer screenshots, images, tables, metrics, and concise status blocks over text-heavy summaries, and return the PDF path instead of a long text report.
---

# Qin Test PDF Report

Use this skill when testing output should be delivered as a PDF report instead of a text-only recap.

## Trigger

Use this skill whenever:

- the user explicitly asks for testing, QA, validation, regression testing, or a smoke test
- the user asks for a test report
- the user asks to see a PDF report
- the user asks for a visual report, report artifact, result report, review PDF, audit PDF, evidence PDF, or proof report
- the user wants verification or review output packaged in a clearer artifact instead of chat text
- a repo instruction says testing should produce a PDF or report artifact
- visual evidence such as screenshots, image comparisons, or tabular pass and fail results would make the test result clearer

## Goal

- Replace text-only test reports with a PDF artifact.
- Make the report easy to scan with status blocks, summary tables, and screenshots when available.
- Choose the report format from the actual cases and evidence. Do not force every report into one fixed PDF layout when a comparison, gallery, prompt audit, or code/API check needs a different shape.
- Keep mixed text-and-image reports visually aligned. When a case includes both explanation and evidence, prefer a stable text block next to a stable evidence block instead of letting paragraphs and images drift into a random flow.
- For comparison reports, always show the before and after states with the real data and images that were compared. Never show only the final result.
- For AI agent or prompt-workflow tests where expected or correct values exist or can be derived from the input, show a direct `correct/agent` or `agent/correct` comparison table in the PDF. Do not show only the agent output; make pass/fail cells visible beside the expected values.
- Reuse successful case-specific formats for similar future requests instead of falling back to the generic compact table format.
- Never report synthetic, assumed, or inferred test outcomes. Only include test cases that were actually executed in the collected run logs.
- When the user asks for a report, treat it as a request for real-time workflow evidence. The primary report content must be the actual live result of the requested workflow, API call, agent call, UI action, generated artifact, comparison, or data extraction, not only a code-verification command.
- Summarize the user's real request near the top of the report when the user asked for an edit, fix, validation target, or specific expected outcome.
- Categorize the report purpose so code-heavy, image-heavy, UI-heavy, and mixed reports do not all look the same.
- Keep the report cache from growing forever by pruning stale cached PDFs once their file age passes 7 days unless the user asks for a different retention rule.
- Keep the chat response short and point to the PDF path instead of pasting a long textual report.
- Keep raw cache artifacts such as CSV, JSON, extracted text, stdout, stderr, and run logs available in the report cache and manifest, but do not list them in chat unless the user explicitly asks for raw files.
- When showing a generated PDF report in chat, include rendered preview image(s) whenever practical; an image preview is preferred over text-only output.

## Workflow

1. Run the requested workflow in real time first and capture its actual input, output, returned JSON, generated files, screenshots, or comparison data. Use pytest, unit tests, lint, smoke tests, or compile checks only as supporting code verification when code was edited; they are not a substitute for the report's main result evidence.
2. Gather evidence:
   - screenshots
   - image comparisons
   - the real visible result requested by the user, such as returned JSON, extracted names, generated assets, API responses, rendered UI state, or comparison tables
   - raw run logs, command output, agent logs, warning/error logs, and saved request/result summaries when available
   - before data, after data, before image, and after image for comparison reports
   - key command outputs
   - summary metrics
   - environment details
   - per-test pass, fail, warning, or skipped status
3. Infer the report purpose from the user's request and the artifacts you collected:
   - `code`: code changes, backend checks, CLI output, logs, tests
   - `ui`: browser UI, layout, form, page, screenshot review
   - `image`: image generation, image edits, visual comparison, before and after checks
   - `api`: request and response validation, route checks, polling flows
   - `document`: slides, spreadsheets, PDFs, exported files, render checks
   - `mixed`: more than one category matters materially
4. Choose the report layout before writing the manifest:
   - use the bundled generator for ordinary compact code/API/UI reports when it fits the evidence
   - use a custom ReportLab/PDF builder when the requested report format, visual comparison, step-by-step evidence, or image-heavy evidence cannot be expressed cleanly by the generic manifest renderer
   - when the user points to a report format they like, treat that format as reusable evidence for similar cases
5. Summarize the user's requested edit or target outcome in 1-3 short lines when the request included a concrete fix, edit, or expected result.
6. Choose an output folder:
   - follow closer repo rules first
   - if the user or repo defines a report folder outside the project, use that folder and do not fall back to the default cache
   - if a repo explicitly forbids `./data/cache` or `./Data/cache`, treat that as a hard output-path rule
   - otherwise default to `./data/cache/qin-test-pdf-report`
   - treat that folder as the report-cache root unless the user explicitly wants another cleanup root
7. Write a manifest JSON that matches [references/report-manifest.md](references/report-manifest.md), including:
   - `purpose`
   - `request_summary`
   - log artifact paths for the run, especially `run.log`, warning/error logs, and any saved per-attempt logs
   - category-appropriate artifacts and tables
8. Generate the PDF:
   - if bundled workspace Python is available, prefer it
   - run `python3 scripts/generate_test_pdf_report.py --input /path/to/manifest.json --output /path/to/report.pdf --cleanup-root /path/to/report-cache-root`
   - if a custom layout is required, write the PDF directly with the same evidence and still store the manifest or source data beside the report artifacts
   - let the generator prune stale cached report PDFs older than 7 days unless the user explicitly wants cleanup disabled or a different retention window
9. Check that the PDF was created and is non-empty.
10. If cleanup ran, keep the new PDF and any recently used PDFs, and only remove stale cached report PDFs from the report-cache root.
11. In the final response, give the PDF path, include a rendered preview image when practical, and keep any text to a brief top-line result unless the user explicitly wants more detail.

## Format Selection

- Pick the layout that best explains the case. A smoke test, API route test, before/after image edit, comparison review, document audit, and UI screenshot review should not all share the same page structure.
- For prompt/source data comparison reports, do not choose a fresh layout. Always reuse the canonical template format from `/Users/qin/QinProject/Muse/MuseAI/data/cache/qin-test-pdf-report/black-floral-lace-bra-compare/black_floral_lace_bra_prompt_pdf_comparison_report.pdf` so repeated prompt-vs-PDF/table/source checks look consistent across runs.
- Use the generic compact case-table layout for ordinary code checks, API checks, and short command validations.
- Use a step-by-step layout when the user needs to understand process, instructions, order of operations, or how the result was produced.
- Use a before/after comparison layout when the user is reviewing an edit, regression, baseline/current result, or visual diff.
- Use an image gallery or screenshot review layout when the evidence is mostly screenshots or rendered UI states.
- Use a side-by-side comparison layout when the reader must compare two or more outputs against the same input, target, or baseline.
- Keep one selected layout internally consistent across that report, but do not treat consistency as a reason to reuse the same layout for unrelated report categories.
- When the default generator cannot express the selected layout clearly, generate a custom PDF while preserving the same report-cache, manifest, cleanup, and verification rules.

## Case-Specific Page Design

- Start each report with clear reader instructions: what is being tested, what to compare, what the labels mean, and how to read the evidence.
- Put setup details near the top when they are required to interpret the result, such as commands, prompts, models, input files, target URLs, expected behavior, or source documents.
- For comparison pages, make each side unmistakable with large side labels, colored headers or borders, and an explicit note when panels share the same source, baseline, or input.
- If a panel is labeled as one result, one side, or one model output, draw only that panel's annotations in it. Do not add reference, expected, baseline, or other-side annotations into that panel unless the title explicitly says it is a combined overlay.
- For step-by-step reports, show the ordered steps as their own section before the detailed evidence. Each step should have a short action, expected result, and actual result when available.
- For image-heavy reports, prefer larger visual evidence with short labels over dense prose. Put the table only where it helps identify coordinates, statuses, or differences.
- For product, garment, generated asset, document-page, or before/after evidence where the full object must be inspected, preserve the complete image on one page. Use manifest artifact fields such as `fit_mode: "contain"` or `preserve_full_image: true`; do not slice or crop these images. Reserve tall-image slicing for long screenshots, chat logs, terminal output, or other scroll-like evidence where continuation pages are expected.
- For MuseAI default BOM names image reports, use the user's generated-asset evidence report style: A3 landscape, image-first, with an overview page and `Generated BOM Assets` pages where each BOM row card shows the cropped source/reference image beside the final generated BOM asset image. Each card should include BOM name, type, pass/warning status, source side, coordinates, cropped reference label, generated asset label, and generated asset path or URL when useful. Store the manifest, raw logs, agent logs, cropped source/reference images, generated final images, rendered preview pages, stdout, stderr, and result JSON beside the PDF in the report cache. Circled BOMNameAgent images may be supporting evidence, but they are not the main default report layout for this request.
- For code/API reports, prefer compact summary tables and command/request/response evidence before screenshots or long logs.
- For MuseAI overall API test reports, use the stable local API template from `/Users/qin/QinProject/Muse/MuseAI/data/cache/qin-test-pdf-report/overall-api-8443-20260511-123918/museai_overall_api_test_report.pdf`: A4 landscape, first-page `Overall Result` and `Run Artifacts`, green/red `Local API Route Status`, `Local APIs Not Working`, then per-route input/output visual evidence pages with real request and response images when available. In the MuseAI repo this template is implemented by `/Users/qin/QinProject/Muse/MuseAI/plugins/muse-ai-plugin/skills/test-api-route-skill/scripts/generate_api_route_report_pdf.py`.
- For document/spreadsheet comparison reports, embed rendered preview images of the generated PDFs, spreadsheets, documents, or slides when practical. Do not replace visual evidence with file paths alone; paths should be supporting metadata under the rendered evidence.
- Add summary pages only when aggregate metrics, failures, warnings, or repeated-case variation need their own page. Do not add summary pages just to preserve a template.
- Keep page orientation flexible. Use landscape pages for side-by-side comparisons, wide tables, and screenshot grids. Use portrait pages for text-heavy steps, document reviews, and long vertical screenshots.
- For table-heavy comparison reports, choose page size, orientation, row chunking, and column grouping dynamically from the data. Use the largest readable table font that fits the page. Split wide tables across logical page groups instead of shrinking every column into tiny text, and split long tables vertically so the table fills the page instead of becoming a small strip with excessive blank space.
- When the user asks for the full comparison table or says a split table is only partial, render a full matrix first, even if it requires A3/A2 landscape, smaller readable fonts, or row chunking. Keep all compared columns visible together in the first matrix view whenever practical.
- For dense expected-vs-actual matrix reports, use compact `expected/actual` proof cells by default, such as `55/55`, instead of stacked `E` and `A` labels unless those labels are explicitly requested. Keep one topic per table, such as values, tolerance, and steps as separate tables/pages, so unrelated comparison topics are not crammed into one matrix. Try oversized landscape pages with large readable fonts, generous row height, stable column widths, and full-page width/height usage. Split into a small number of full-page logical topic tables when a single page would mix topics or make text harder to read.
- For MuseAI one-case universal POM testing reports, use the saved template `/Users/qin/.codex/skills/qin-test-pdf-report/references/templates/universal_pom_one_case_template.pdf` and mirror its A3 landscape layout: compact summary, exact prompt text shown large on page 1, a dedicated full-size prompt page near the front, compact size-structure/debug-config table, coordinate evidence when flat sketches exist, then full-width POM proof tables. Preserve the prompt's line breaks and visible table shape; do not bury the prompt only in a tiny setup table, artifact path, or raw log reference. Proof cells must record `correct / agent / final` horizontally, where `correct` is prompt/config truth, `agent` is the raw size-range or size-step agent value, and `final` is the value after `agent_universal_measurement_size.py`. Do not add `PASS` text inside green proof cells.
- When a comparison contains multiple prompt table sections, such as BOM plus POM, render a full table for every section before failure-only summaries. Do not omit BOM rows because a POM matrix exists, and do not replace a full BOM table with only warnings or mismatches. Each prompt BOM row should remain visible with its matched source/PDF row, status, and note.
- For short comparison tables or split matrix pages, scale row height and type size to fill most of the usable page height. Do not leave a large blank lower half after a table unless the remaining space is intentionally reserved for evidence or another section.
- Full-table report pages must use the full page, not only the top band or a narrow center strip. Scale row heights, column widths, font size, page size, or row/column chunks so the table fills most of the usable page width and height. If the page size or orientation changes, recalculate table column widths and row heights from the usable page area instead of reusing fixed widths from the old layout. If one table would leave large blank space, increase row height, column width, and padding; if it becomes unreadable, split it into multiple full-width, full-height pages with repeated headers.
- Do not make dense tables readable by placing a tiny table on an oversized page. If a table looks like a small top band with excessive blank space, rebuild it with larger fonts and row heights, split wide size/value columns into logical page groups, or use a smaller page size so the table is reviewable at normal zoom.
- If the user says a PDF page, detailed report, or table page is too small, regenerate the report from the saved run evidence immediately with a larger readable layout instead of telling the user to zoom. Use A2 or A1 landscape for dense detail reports, split each topic into its own full-page table, increase font size and row height, and render fresh preview images from the enlarged pages.
- For prompt/table comparison reports, preserve the user's pasted table as the source-of-truth shape. Keep the user's row names, column headers, column order, and cell values as the primary proof table. If the current source uses a different size system and a clear mapping is needed to check values, use the mapping for comparison but keep the user's table headers visible and score the actual cell values, not the header-system difference.
- For prompt/source data comparison reports, keep the black floral lace bra report as the stable visual template: A2-style landscape pages, light high-contrast top header, compact `Overall Result` page, full-width proof tables, then visual source evidence pages. The default page order is `Overall Result`, `Prompt Source Text`, full BOM comparison pages, `POM Name Comparison`, `Full POM Value Matrix`, source table evidence, and source image/swatch evidence. If the data is not BOM/POM, map it to the nearest equivalent full comparison table and keep the same overview, prompt-source, proof-table, and source-evidence rhythm instead of changing to a different layout.
- For prompt/source data comparison reports, always add the full original user prompt as a readable page near the front. Preserve line breaks and table text enough that the PDF can be reviewed without relying on chat history.
- Keep canonical prompt/source table columns stable when those sections exist. BOM and requirement pages must use proof-cell columns: `#`, `Component prompt/source`, `Details prompt/source`, `Color prompt/source`, `Placement prompt/source`, `Status`, `Note`. POM names: `#`, `Prompt POM Name`, `PDF/Source POM Name`, `Status`. POM matrix: `#`, `POM`, `Tol`, prompt-size/source-size proof columns, `Status`.
- Keep canonical rendering stable: light high-contrast table headers instead of black or very dark header bands, full-page width tables, readable wrapped cells, status-colored rows/cells, `prompt/source` proof values, mapped headers like `XXS/2XS`, source-only headers like `?/5XL`, and missing cells like `value/?` or `?/value`. Fill proof-cell backgrounds directly: green for matching `prompt/source` cells, red for contradictory non-missing values, and yellow for missing, source-only, partial, or ambiguous cells. Identical explicit placeholders such as `TBD/TBD`, `N/A/N/A`, `G/A/G/A`, `blank/blank`, `empty/empty`, or `cancel/cancel` are source-of-truth matches and must be green `PASS`, not yellow warnings. Do not replace the canonical full tables with a short mismatch summary unless the user explicitly asks for a summary-only report.
- Add a compact color legend on the overview page for prompt/source data comparison reports: green `PASS`, yellow `WARNING`, and red `FAIL`. Show the legend even when the current result has no red failure cells.

## Report Rules

- Prefer visual evidence over paragraph summaries.
- Make the requested real-time result visible in the report body. If the workflow returns JSON, tables, names, IDs, URLs, measurements, images, or generated files, show those concrete values directly in a readable table or panel before any pytest, smoke-test, lint, or compile output.
- For API tests that return media/resource URLs in request or response payloads, include those URLs as concrete values in the case `request`/`response` fields (or `input`/`output`) so the PDF carries retrievable evidence links.
- Prefer concrete examples over abstract summary text. Show the real given text, real returned text, and real evidence images whenever they are available.
- For comparison cases, render explicit `Before` and `After` rows before any final result row. Include `before_image_path` and `after_image_path` when images exist, and mark missing before/after evidence instead of silently dropping it.
- For table comparison cases, show mismatches directly against the user's table. Cells should be readable as `user_value/current_value`, and wrong cells should be listed under the exact user row and column names. If an inferred size mapping is used, show the mapped source size clearly in the header or cell note and make the value comparison the main pass/fail basis. Do not count a header-system mismatch as a value failure unless the user asks for an exact-header audit.
- In prompt/source table comparison reports, use one consistent table color contract for affected proof cells and status cells: green `PASS` background for fully matching values, including identical explicit placeholder values such as `TBD/TBD`; red `FAIL` background for wrong contradictory non-missing values; and yellow `WARNING` background for missing, source-only, partial, or ambiguous evidence. Use yellow for `prompt_value/?` when the source table is missing a prompt value, yellow for `?/source_value` when the source has a value or column missing from the prompt, and yellow for partly correct or partly evidenced matches. Reserve red `FAIL` for contradictory non-missing values unless the user explicitly asks for strict exact-shape failure scoring. Score against the prompt/source text as the source of truth; do not turn matching placeholders into warnings because a numeric or physical local value could be inferred.
- For BOM comparison tables, show the full prompt BOM table, not only failures. The main BOM/requirement table must use direct prompt/source proof cells for component/name, details/description, color/Pantone, and placement/count/position when useful. Avoid separate prompt-side and source-side columns as the primary proof because they make missing and added source data hard to see. Use cells such as `ALLOVER PRINT CREPE/ALLOVER PRINT CREPE`, `Waist with all around gathers/?`, `?/Back Neck Zipper`, and `Not provided/?`.
- For mapped POM value matrices, especially when the prompt size range is not the same system as the source size range, use a full matrix with column headers in `prompt_size/source_size` form, such as `70A/S` or `85D/XL`. This applies to bra/cup sizes, numeric sizes, kids sizes, regional sizes, or any other prompt size range mapped to apparel sizes or another source size range. Never show only the prompt size when a mapped source size exists; if the source size label is long, wrap the header to two lines but still show both sides. Value cells must always use `prompt_value/source_value` order, with the prompt value on the left and source/PDF value on the right.
- If the source table has extra size columns that no prompt size maps to, include those source-only columns in the full matrix when the user asks to see the full table. Label them as `?/source_size`, such as `?/5XS` or `?/4XL`, and show cells as `?/source_value` so the user can inspect extra source data without confusing it with prompt-required values.
- Include screenshots when available.
- Use tables for test case status, metrics, and environment details.
- Put the overall status near the top.
- Put the report purpose and user-request summary near the top when known.
- Keep per-test descriptions short and concrete.
- Make section titles explicit. Use clear labels such as `Summary`, `Testing Summary`, `Testing 1`, or `Evidence` instead of vague mixed-content headings.
- Default each test case to one compact table, not mixed heading text plus loose rows.
- Put the test-case title and status in the same first row, for example `Testing 1: Login flow | PASS`.
- For function or API checks, keep the row order predictable:
  - first row: title row with the function or case name and status
  - second row: `Input`
  - third row: `Output`
  - only after that: short supporting detail rows only when the report explicitly needs detailed mode
- Keep per-case tables compact by default. The normal case should stop at title, `Input`, and `Output`.
- Do not print `Summary`, `Scenario`, `Response Length`, `Input Image Size`, `Notes`, or other support rows for every case by default.
- Only show extra per-case rows when the manifest explicitly asks for detailed output or when the case would otherwise have no real result row.
- Do not default to ambiguous `Input` and `Output` labels.
- Default the main case rows to real example content first. Prefer plain `Input` and `Output` labels when the case is showing what a function or API was given and what came back.
- Only fall back to summary-style `Check` and `Result` rows when the report does not have a better concrete example to show.
- When the manifest still uses `objective` and `result`, treat them as fallback summary rows unless the case explicitly provides more concrete example fields.
- If a case has both concrete example text and a short explanation, show the concrete example rows first and keep the summary or finding as one short secondary row.
- When the user asks to include model names, prompts, system prompts, request payloads, or other long setup text, make that setup visible near the top as its own clearly named case or artifact. Do not bury it only in `environment`, a caption, or a compact metadata row. For long prompts, include both real text in the case rows and a readable prompt-card image artifact when practical.
- Keep case rows in strict label/value table form such as `Check | ...`, `Result | ...`, `Command | ...`, and `Note | ...`.
- Keep labels bold in the left column so the user can immediately tell title, input, output, and supporting fields apart.
- Add one short legend near the testing section that explains what the row labels mean.
- When API semantics matter, make the legend explicit: `Input` means what the function sent into the API or test path, and `Output` means what came back from the API or function.
- Always include clear instructions or reading steps when the report has multiple panels, repeated cases, or non-obvious evidence. The reader should not have to infer which image/table/side matters.
- Keep table and case-row fonts modest so long evidence rows stay readable without oversized text.
- For dense proof tables, prefer fewer columns with larger readable cells over a single over-wide table. If a table still leaves most of the page blank after fitting, increase font size, row height, or split the section into larger visual blocks that fill the page.
- Vertically center table cell content by default. Do not pin short label cells to the top when the row height grows from wrapped content in another column.
- Apply the same vertical-centering rule to top meta banners as well. If a banner has a fixed-height background bar, center the text within that bar instead of leaving it visually top-weighted.
- Center the full top meta-banner line within the bar, not just the cell box. Do not leave the purpose and status text left-aligned inside a centered banner row.
- Keep the first page compact. Do not spend a large vertical block on giant title styling or repeated full-width banners when one compact header line will do.
- Prefer one short meta banner such as `Purpose | Status | counts` instead of multiple oversized banner rows.
- Collapse the top summary into a few rows such as `Goal`, `Result`, and `Context` instead of separate `Overview` and `Environment` tables when that would only repeat basic metadata.
- Merge repeated rows of the same kind when the meaning stays clear, especially multiple `Note` rows. Prefer one `Notes` row over several separate `Note` rows.
- Keep one consistent label/content column split across the report for label-value tables. Do not let the `Summary` table and per-case tables use different label widths.
- Keep the first label column compact across all label/value tables. The label column should only be wide enough for short row names such as `Goal`, `Result`, `Check`, or `Command`.
- If a status-only second column would make one table visually inconsistent with the rest of the report, prefer a single full-width row with inline status such as `Case name | PASS`.
- If a table uses 2 or 3 columns, keep the first column as the label and keep the remaining columns limited to short status, compare, or value fields. Do not use a wide freeform prose column as a `Result` dump.
- Do not render case bodies as inline prose such as `Input: ...` inside one text block. Use real table cells.
- Keep cell padding tight and let tables use the page width so wrapped text does not leave large blank areas.
- Keep the report easy to scan for a quick result read. Bias toward fewer rows, not more rows, in ordinary pass cases.
- If an image path is missing or unavailable, keep the row in the report and mark the artifact as missing instead of silently dropping it.
- When a code or API report has no natural product image, include screenshot-style evidence images for important command output, log excerpts, payloads, or diffs whenever possible.
- Keep evidence images visually aligned to the main report content width, and prefer compact landscape evidence images over oversized tall screenshots when the content is mostly text.
- For tall top-level evidence images, split the image into full-width readable slices only when the artifact is scroll-like evidence such as a long screenshot, chat log, terminal output, or web page. For product/garment/generated-asset evidence, keep the whole object visible on one page with `fit_mode: "contain"` or `preserve_full_image: true`.
- If an evidence image belongs to one specific test case, place it under that case instead of putting it in a generic top-level evidence section.
- If you render a function example image, mirror the same order as the table above it: title row, `Input`, then `Output`.
- Keep function example images visually the same usable width as the main report tables, and wrap or resize text so no panel content clips or overflows its box.
- When a case input includes a real source image, prefer embedding a compact thumbnail directly inside the case table's `Input` row. Only use a separate function example card if it adds value beyond the table.
- Avoid long redundant captions under function example images. If the title and image already make the meaning clear, omit the caption instead of repeating the same sentence below the card.
- If a test did not run, say `skipped` rather than pretending it passed.
- For image or UI reports, bias toward bigger visual evidence blocks before dense detail tables.
- For before/after image reviews, use a comparison case rather than a final-only evidence block: pair the original data and image with the revised data and image so the change is reviewable.
- For code or API reports, bias toward compact summary tables, command evidence, and key output fields before long screenshot galleries.
- Do not use a side-by-side text column plus evidence column layout for ordinary case summaries when a full-width row table is clearer.
- Keep related content together on one page whenever practical. Do not split a visual panel from its legend, table, or instructions onto another page if changing orientation, scaling, table density, or page layout would keep the section whole.
- Keep the selected case layout consistent across pages inside one report so the same kinds of content appear in the same places.

## Output Rules

- Generate a PDF report whenever the user asked for testing or a test report.
- Do not stop at a text-only report when a PDF was requested or implied by the testing workflow.
- Show the report with preview image(s) in chat when practical, not only a text path. Render and show every report page preview whenever practical, not only the first page.
- When reports are stored in a dedicated cache such as `./data/cache/qin-test-pdf-report`, prune stale cached report PDFs older than 7 days by file age.
- Keep the chat summary short. The PDF is the report.
- Do not list internal cache files, raw CSVs, extracted text, logs, or manifests in the chat response unless the user asks for those files. The PDF may reference supporting artifacts internally when useful.

## Guardrails

- Do not replace the PDF with a long text-only recap.
- Do not use pytest, unit-test, lint, compile, or smoke-test output as the main report when the user asked to see a workflow result. Those checks can prove code health, but the report must still show the real requested result.
- Do not let comparison, regression, baseline, before/after, or visual-diff reports collapse to only a final output row.
- Do not omit known failed or skipped cases just to make the report look cleaner.
- Do not silently drop missing screenshot paths; mark them as missing in the report.
- Do not ignore closer repo rules for output paths or artifact folders.
- Do not create report PDFs in `./data/cache` or `./Data/cache` when user or repo instructions name a different report destination.
- Do not invent a fake request summary. If the user goal is unclear, say it is inferred or leave it blank.
- Do not keep every report category in the same rigid layout when one category clearly needs more visuals or more technical tables.
- Do not force the generic manifest/table layout when the user's case needs a custom comparison, gallery, step-by-step walkthrough, audit view, or other case-specific PDF format.
- Do not ship a report with awkward page breaks that separate a section's instructions, visual evidence, and supporting table when a reasonable portrait/landscape/layout change would keep them together.
- Do not sweep arbitrary user folders for old PDFs. Only clean the dedicated report-cache root for this skill or a cleanup root the user explicitly chose.
- Do not delete the newly generated PDF or any report PDF whose file age is still within the last 7 days.

## Verification

- Confirm the manifest JSON exists before building the PDF.
- Confirm the output PDF exists and is non-empty after generation.
- Render or open representative PDF pages yourself and check that the layout is readable. For custom or visual reports, inspect at least one page from each major page type, not only the first page.
- Check that important sections fit on a page without broken evidence. If content spills awkwardly, rebuild with portrait or landscape orientation, smaller but readable images/tables, or split the section deliberately with repeated headers and clear continuation labels.
- Parse the PDF text when practical to confirm key labels, instructions, and setup details are present.
- When cleanup is enabled, confirm stale cached report PDFs older than the retention window were removed only from the report-cache root.

## Continuous Update

- When the user asks to change the PDF report format, sections, categories, or evidence style, treat that as a request to improve this global skill itself, not just one output file.
- Fold reusable improvements back into this skill, its manifest reference, and its generator script with the smallest general change that will help future runs.
- When a new testing/report category appears, add the category support here instead of solving it as a one-off workaround.

## Reference

- Read [references/report-manifest.md](references/report-manifest.md) for the manifest shape and examples.
- MuseAI one-case universal POM report template: [references/templates/universal_pom_one_case_template.pdf](references/templates/universal_pom_one_case_template.pdf)

## Examples

- "Smoke test this feature and give me a PDF report."
- "Run QA on this page and make the result visual."
- "Validate the app and stop sending me a text-only test summary."
- "Check this image edit and make the PDF emphasize before and after visuals."
- "Test this code fix and summarize the user-requested edit near the top of the report."
- "I want to see a PDF report."
- "Give me a visual report instead of text."
- "Make the review result a PDF with screenshots and tables."

---
name: test-skill
description: "Executor skill under workflow-skill for testing and calibrated report evidence. Use when workflow-skill routes completed work into proof: code, UI, scripts, automations, generated assets, or content have been created or changed; the user asks to test, verify, QA, smoke test, validate, prove, or generate a report; or completed work needs real executable evidence. Requires real runnable tests with concrete generated inputs, real inputs/outputs, the exact command/tool used, and a clear pass reason instead of mock-only, signature-only, or pass/OK-only checks. Chooses the evidence format by complexity: simple results stay in a few chat lines, while PDF/report artifacts are reserved for long data, table-heavy evidence, image/UI/document comparisons, or explicit artifact requests. Its evidence routes are multi-select: combine every test/report route needed by the artifact."
---

# Test Skill

Use this as the single testing and reporting executor selected by `workflow-skill`. It merges completion verification with calibrated evidence output: short chat evidence for simple results, lightweight tables when helpful, and PDF reports only when the evidence benefits from an artifact.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

This skill covers many evidence types and report layouts. Do not run every test type or force every report shape. Select every evidence route needed by the artifact, and combine routes when the work spans types such as code plus UI or document plus PDF. Use the smallest real test set and evidence format that proves the user's requested behavior. When a formal report is generated, every passing case still needs real `Input`, `Used`, `Output`, and `Why Pass` evidence.

## Trigger

Use this skill when work needs proof: code changed, UI changed, a script or workflow was created, a generated artifact needs QA, the user asks for testing or reporting, or another skill has defined a pass target that needs real evidence.

## Core Rule

Do not finish because the edit is written. Prove the work with a real executable test. Match the evidence format to the complexity: a simple successful check can be reported in a few chat lines; use a table, Markdown summary, or PDF only when that makes the evidence easier to review.

Every generated report must show the real evidence, not a vague `OK`, `PASS`, or method-only claim. For each passing case, list:

- `Input`: the real input that was given, such as a file path, image, URL, prompt, request payload, command input, code snippet, or concrete test data
- `Used`: the actual tool, command, script, browser route, model call, API endpoint, or local workflow used to run the check
- `Output`: the real output that came back, such as stdout, JSON, rendered file, screenshot path, generated image, URL response, return value, diff, or produced artifact
- `Why Pass`: the exact acceptance reason, tied to the user's requirement and the observed output

If the evidence is an image, include the image path or rendered preview. If it is a link, include the exact URL and observed response or page state. If it is code, include the code path or snippet plus the command that ran it. If it is a result, include the actual value, log excerpt, file, screenshot, or artifact that proves the result.

For code changes, the primary verification must be a small real use of the changed code:

- Write or run a small script, command, browser flow, app flow, API request, CLI invocation, or generated-input example that exercises the actual changed behavior.
- Do not stop at checking whether a function exists, whether a method accepts parameters, whether imports work, or whether a type checker/linter passes.
- Do not call mock-only tests enough when the real behavior can be exercised locally.
- If the code needs an image, URL, file, JSON, audio, PDF, browser page, API payload, or other input, create a concrete temporary input yourself and run the real path against it.
- If a service or external dependency cannot be reached, run the closest real local path and state exactly what external part remains unverified.

## Workflow

1. Identify the user requirement and the behavior that must work.
2. Choose the smallest real test that proves that behavior.
3. Generate any required concrete inputs, such as temporary images, local files, JSON payloads, HTML pages, localhost URLs, sample PDFs, or API bodies.
4. Run the actual changed path with those inputs.
5. Capture evidence: real input, command/tool used, output, generated files, screenshots, returned JSON, rendered pages, logs, pass/fail status, and the reason the observed output satisfies or fails the requirement.
6. If the test fails and the fix is in scope, fix the code and rerun the real test.
7. Choose the evidence format. Use chat for simple results; use Markdown/table summaries for medium evidence; generate a PDF only when long data, many rows, screenshots, visual comparisons, rendered documents, or an explicit artifact request make an artifact easier to review.
8. In the final response, state what changed, what real test ran, what passed or failed, where any report artifact is, and what remains unverified.

## Real Test Standards

A good test proves the feature can actually be used:

- Python function: run a short script that imports the real module and calls the changed function with concrete data.
- CLI: execute the CLI with a temporary input file and inspect the real output file or stdout.
- API route: send a real request to the local route or local handler and show request/response evidence.
- UI: open a real page or local preview, interact where needed, and capture screenshots.
- Image code: create or use a small real image, run the code, and inspect the generated output.
- URL code: serve or use a real reachable local URL when possible; if external network is unnecessary, create a local HTML/file URL.
- PDF/document code: create a small document or PDF, run the changed path, and inspect the generated artifact.
- Unity/editor code: verify in the live Unity Editor when behavior depends on editor rendering, inspector controls, custom windows, import, compile, or generated previews.

Supporting checks such as lint, type check, unit test, import check, build, or syntax check are useful, but they do not replace a real usage test when one is practical.

## Report Format Decision

Do not generate a PDF report by default. For easy results, report the real evidence in a few concise chat lines: the command or tool used, the real output, and why it passes.

Generate a PDF report when:

- the user explicitly asks for a PDF, downloadable report, or artifact
- evidence is long, table-heavy, multi-case, or easier to scan as structured rows
- the output is visual, document-like, image-based, UI-based, or needs side-by-side comparison
- screenshots, rendered pages, before/after images, or document previews need to be reviewed together
- a repo or project rule asks for a report artifact

If the user asks for a "report" and the evidence is short, prefer a concise chat or Markdown report unless they specifically ask for a PDF/artifact.

Any generated report must show real evidence, not only command names:

- user request or expected outcome
- real test input, payload, artifact, image, URL, code path, or prompt
- exact command, script, tool, browser route, model/API call, or workflow used
- real output/result, including the returned value, stdout, JSON, screenshot, rendered artifact, generated file, or URL/page state
- why the output passes or fails the user's requirement
- pass/fail/warning/skipped status
- generated files or screenshots when relevant
- raw logs or run artifacts stored beside the report when useful
- remaining unverified scope when something could not be tested

Do not make a passing row whose output is only `OK`, `done`, `works`, `pass`, or similar. Those words may appear only after the report shows what was run, what came back, and why the observed output satisfies the requirement.

Use the bundled manifest/report generator for ordinary PDF reports:

```bash
python3 scripts/generate_test_pdf_report.py --input /path/to/manifest.json --output /path/to/report.pdf --cleanup-root /path/to/report-cache-root
```

Read `references/report-manifest.md` when building a manifest.

The generator rejects passing cases that do not include real `Input`, `Used`, `Output`, and `Why Pass` evidence, or whose output is only a bare status word such as `OK`, `PASS`, `done`, or `works`.

## Report Layout

Choose the report shape from the evidence when a report artifact is warranted:

- Code/API/CLI: compact summary table, real command/input/output, key logs, and status.
- UI/browser: screenshots, layout notes, interaction results, and console/runtime evidence.
- Image/edit/generation: before/after or input/output images with readable labels.
- Document/PDF/spreadsheet/slides: rendered page previews and file paths.
- Comparison/audit: expected vs actual tables with visible pass/fail cells.
- Mixed workflows: combine the smallest layout that makes the result reviewable.

Do not force every report into one fixed layout. Do not replace real workflow evidence with only lint, pytest, or compile output.

For PDF report tables, use adaptive full-page layout. The table should fill the useful page area instead of sitting as tiny text at the top or overflowing as oversized rows. Choose page size, orientation, font size, row height, column widths, and page splits from the amount of data:

- If the table has little data, increase font size, row height, and spacing so it uses most of the page width and height.
- If the table has many rows or long cells, reduce font size only enough to stay readable, wrap text cleanly, and split into logical continuation pages.
- Keep related proof columns and status/reason columns together when practical; do not scatter one small table across several sparse pages.
- Render preview pages and reject reports with unreadably small text, excessive blank lower page space, clipped text, or wildly inconsistent table scale between pages.

## Output Rules

- Keep simple evidence in chat; do not create a PDF just to repeat a short pass result.
- When a PDF is generated, keep the chat summary short, return the PDF path, and show rendered preview image(s) when practical.
- Keep raw cache artifacts available beside the report, but do not list every internal file unless asked.
- If no PDF can be generated, report the exact blocker and still provide the real test evidence in chat.

## Verification

- Run the selected real test with concrete inputs before generating a passing report.
- Parse or inspect the generated PDF when one is produced, and confirm every passing case includes `Input`, `Used`, `Output`, and `Why Pass`.
- If a test fails and the fix is in scope, fix the artifact and rerun the same real check.

## Guardrails

- Do not claim completion from a mock-only test when a real local test is practical.
- Do not claim completion from method-parameter, signature, import, or lint checks alone.
- Do not generate a PDF report for a simple result that is clearer as a few lines of chat.
- Do not generate a passing PDF that lacks real `Input`, `Used`, `Output`, and `Why Pass` evidence for each passing case.
- Do not use `OK`, `PASS`, `done`, or a green status as the whole result.
- Do not invent inputs, outputs, screenshots, or pass/fail results that were not actually produced.
- Do not hide failed or skipped tests.
- Do not silently drop missing screenshots or artifacts; mark them missing.
- Do not delete newly generated reports or recent report artifacts.
- Do not sweep arbitrary folders for cleanup; only clean the selected report-cache root.
- Do not push or publish code unless the user or active workflow explicitly asks for it.

## Examples

- "I fixed the Python function." -> create a tiny concrete input, call the real function, inspect output, and summarize the command/output/pass reason in chat unless the evidence is complex.
- "This image parser now supports PNG." -> generate a small PNG, run the parser, show returned data and image evidence.
- "This URL scraper changed." -> serve a local HTML page or use a reachable URL, run the scraper, show extracted output.
- "Fix the page layout." -> run the local app, capture before/after or current screenshots, and report layout status.
- "Give me a QA report." -> run the real workflow, choose chat/Markdown/PDF based on evidence size, and return a PDF only when visual, table-heavy, long, or explicitly requested.

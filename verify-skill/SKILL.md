---
name: verify-skill
description: "Verification executor selected by workflow-skill. Use when work needs proof, tests, QA, review, UI/visual checks, artifact verification, regression comparison, or failure triage. Default to one mini real test; use real result testing for major or user-requested result tests. Require concrete input/output evidence and Obsidian regression sweeps when relevant."
---

# Verify Skill

Use this as the single verification executor selected by `workflow-skill`. It decides what must be checked, runs or coordinates the real evidence check, chooses the evidence/report format, loads specialized references, and decides whether the user's requested outcome is actually satisfied.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

This skill is a verification router with multiple routes. Do not run every route for every task. Select every route that matches the artifact and requested outcome, and combine routes when the request spans real executable proof, report generation, functional result, regression comparison, UI/visual quality, local script/process, code behavior, skill/instruction, generated artifact, document/report, or mixed work. Load only the relevant reference files and specialized checks for those routes.

## Trigger

Use this skill when the task is about correctness, real testing, proof, quality, audit, validation, UI review, artifact review, report evidence, or confirming that a finished workflow meets the user's stated target. Do not use this as the primary optimization skill; `optimization-skill` decides and implements reusable workflow optimization, then this skill verifies that the optimized route preserves the same behavior.

## Core Rule

Verify the user's actual outcome, not just the method. A check is only useful when it answers: "Does the thing now work, look, read, or behave the way the user asked?"

- Prefer real artifacts, real screenshots, real command output, real files, real browser states, and real run logs.
- Do not call something verified only because code compiles, a method accepts arguments, or a file exists.
- If the task produced code, scripts, browser flows, automations, reports, or generated artifacts, run the smallest real usage check that exercises the changed path with concrete inputs.
- Verification evidence must list the real input, method, output, and pass reason when a formal report is generated. A green status, `OK`, `PASS`, or method name alone is not evidence.
- If the task produced visible output, run the visual verification route below before calling the artifact acceptable.
- If the user asks whether the result matches prior behavior, preserve the current intended behavior, or "still works", compare against an available baseline such as prior screenshots, golden outputs, existing tests, git-visible behavior, saved examples, user-provided context, or documented expected behavior. If no baseline exists, state that exact gap instead of implying regression coverage.

## Default Mini Real Test Rule

The default verification shape is one mini real test: the smallest executable or inspectable check that uses real input/output and can catch the changed path breaking. For minor edits, low-risk changes, and not-important updates, one mini real test is enough when it directly exercises the affected behavior.

Use real result testing, not just a mini check, when the update is major, changes user-visible behavior, touches broad/shared code, affects data/security/deployment/public APIs, changes UI/generated artifacts, or when the user asks to test the result after editing. A real result test must exercise the actual edited result the user cares about, not a substitute path.

Do not inflate verification with many fake, shallow, or status-only checks. A compile, import, lint, existence check, route listing, mock-only call, or bare `PASS` output can support verification, but it cannot replace the one real mini test when a real test is practical. If only a shallow check is possible, say exactly what remains untested instead of saying the result passed.

## Pass Return And Background Closeout

When verification passes, return the pass verdict and essential evidence to `workflow-skill` immediately so the user can receive the result. Do not keep the user waiting while doing non-user-facing closeout.

Post-pass DailyLog entries, wiki/log updates, Obsidian memory pages, Markdown summaries, optimization notes, report indexing, and similar records are secondary. Run them in a background/non-blocking route when available. If no background route is available and the record is not required for the user-facing deliverable, defer or skip it instead of delaying the final answer. If a higher-priority environment rule requires a minimal memory closeout before final response, keep it brief.

Model rule: newest/current selected reasoning models are for verification judgment, comprehensive review, image/visual assessment, and final pass/fail decisions only. Any post-pass log/wiki/DailyLog/Obsidian/Markdown drafting or file editing is Spark-default execution and must use `GPT-5.3-Codex-Spark` (`gpt-5.3-codex-spark`).

## Obsidian Regression Sweep

When verifying connected project work, repeated workflows, generated artifacts, UI/visual/Unity/image/browser/deployment work, or global skill behavior, treat available Obsidian project memory as a final regression baseline, not just background context.

1. If `/Users/qin/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyAILLM` exists and the task maps to a known project or skill area, read the matching folder instructions first, then inspect the project or skill index, recent DailyLog entries, `wiki/log.md`, `Skills/Failure Learning.md`, and any directly named feature, asset, file, route, or artifact pages. Use targeted search with touched file names, artifact names, feature names, route names, and user-facing labels.
2. Build an Obsidian regression checklist before the final pass verdict. Include every relevant item in scope:
   - repeated AI-caused failures with at least two distinct Obsidian records for the same or substantially same user-visible issue;
   - prior user corrections, "Next-time rule", "Lesson", "Do not", "Never", "must", or "must not" records tied to touched files, generated artifacts, UI/visual state, prompts, project rules, or changed behavior;
   - previously fixed bugs that the current code, prompt, generation, or workflow could plausibly reintroduce, even when the old issue has only one strong record.
3. For each checklist item, define the expected preserved behavior, prohibited regression, exact evidence needed, and source note path or heading. Then run or inspect the strongest practical evidence for every item, not a sample. Mark each item `pass`, `fail`, `blocked`, or `not applicable`; `not applicable` requires a concrete scope reason.
4. Do not pass verification if any applicable checklist item is untested, lacks evidence, or fails, even if ordinary tests, file existence, screenshots, metrics, or the main requested change pass. This is a regression failure because the current work may have brought an old AI mistake back.
5. If the sweep fails and generation or repair is in scope, fail the current verification, create an avoidance brief that includes all failed or unverified checklist items, run one targeted regeneration or repair pass with that brief included in the prompt or implementation instructions, then rerun the full Obsidian regression checklist plus the normal evidence checks.
6. If no relevant Obsidian records exist, or the vault or folder is unavailable, state that no Obsidian regression baseline was found and continue normal verification.
7. Record in the verification output: searched sources, checklist items, source note paths, per-item verdicts, evidence used for each item, avoidance brief, retry action if any, and remaining unverified scope. Summarize sanitized lessons only; never copy secrets, credentials, auth files, raw transcripts, or sensitive private logs from the vault.

## Feasibility And Repair Loop

Verification includes active recovery when a failure is theoretically solvable. Do not stop at "it failed" when safe, task-scoped repair attempts are available.

1. Reproduce the failure with the smallest real input that still shows the problem.
2. Classify the blocker:
   - **Fixable in scope**: code error, broken selector, bad layout, missing generated file, wrong command, bad local script arguments, flaky local state, missing local cache, stale dependency, browser console error, failed PDF parse, or incomplete report evidence.
   - **Potentially fixable with alternate route**: UI needs browser inspection, local app state needs computer/browser control, logs/history may reveal a prior working state, docs or package behavior may have changed, network data is needed, or a different implementation path can satisfy the same user goal.
   - **Not logically solvable by Codex alone**: missing user token, private website/account access not granted, required paid service unavailable, contradictory requirements, missing source artifact that cannot be recreated, external production permission not approved, or a task that would require exposing secrets.
3. For fixable cases, try a bounded repair loop:
   - inspect error logs, stack traces, console output, network failures, generated reports, cache contents, previous run artifacts, and relevant git/history evidence;
   - try a direct fix when the cause is clear, then rerun the same verification;
   - if the direct route fails, try a different safe route such as browser automation, in-app browser inspection, computer control, local script adjustment, alternate library/API, official docs, current web search, or a simpler implementation that still meets the user's target;
   - create missing test inputs, sample files, images, URLs, or local fixtures inside `cache/` when the real workflow needs them and the user did not provide them;
   - keep each attempt tied to the original pass target instead of drifting into a different goal.
4. Stop and ask the user only when the remaining blocker is not logically solvable without user-controlled access, approval, payment, secrets, or a missing source artifact. State the exact missing condition and the command/page/evidence that proved it.
5. Record every failed attempt that materially changed the diagnosis: input, method used, observed output, why it failed, next route tried, and final stop reason or pass reason.

Use this loop before returning a fail verdict for code, UI, local scripts, reports, generated assets, browser flows, and skill/process verification.

## Workflow

1. Identify the user's requested outcome, background context, and artifact that should prove it.
2. Classify the verification type: real executable proof, functional result/regression, visual/UI, local script/process, code behavior, skill/instruction, generated file, document/report, report artifact, or mixed.
3. Run the Obsidian Regression Sweep when the task has project, skill, repeated-workflow, generated-artifact, UI/visual, Unity, image, browser, deployment, or automation context.
4. Load only the reference needed for that type.
5. Build a concrete check with real input, real output, and pass/fail criteria.
6. Run or inspect the actual artifact, not a mock substitute, when local execution is practical.
7. If the check fails, run the Feasibility And Repair Loop before returning a fail verdict.
8. Record what was given, what tool/command/workflow was used, what came back, and why that output satisfies, fails, or remains blocked.
9. If the check fails and a fix is in scope, fix the artifact and verify again.
10. Report what passed, what failed, what was attempted, what remains unverified, and where the evidence lives. After a pass verdict, return the result immediately; route non-user-facing logging/wiki/Markdown closeout as background work when possible.

## Real Evidence And Report Generation

Use this route whenever work needs proof: code changed, UI changed, a script or workflow was created, a generated artifact needs QA, the user asks for testing/reporting, or another skill has defined a pass target that needs real evidence.

### Real Evidence Standards

Do not finish because the edit is written. Prove the work with a real executable or rendered check. Match the evidence format to the complexity: a simple successful check can stay in chat; use a table, Markdown summary, or PDF only when that makes the evidence easier to review.

Scale from the Default Mini Real Test Rule: one focused real check for routine changes, broader real result testing only for major, risky, user-requested, or failing cases.

Every generated report must show real evidence. For each passing case, list:

- `Input`: the real file, image, URL, prompt, request payload, command input, code snippet, or concrete test data
- `Used`: the actual tool, command, script, browser route, model call, API endpoint, or local workflow used
- `Output`: the real stdout, JSON, rendered file, screenshot path, generated image, URL response, return value, diff, or produced artifact
- `Why Pass`: the exact acceptance reason tied to the user's requirement and observed output

For code changes, the primary verification must exercise the actual changed behavior:

- Python function: run a short script that imports the real module and calls the changed function with concrete data.
- CLI: execute the CLI with a temporary input file and inspect the real output file or stdout.
- API route: send a real request to the local route or local handler and show request/response evidence.
- UI: open a real page or local preview, interact where needed, and capture screenshots.
- Image code: create or use a small real image, run the code, and inspect the generated output.
- URL code: serve or use a real reachable local URL when possible.
- PDF/document code: create or use a small document or PDF, run the changed path, and inspect the generated artifact.
- Unity/editor code: verify in the live Unity Editor when behavior depends on editor rendering, inspector controls, custom windows, import, compile, or generated previews.

Supporting checks such as lint, type check, unit tests, imports, builds, or syntax checks are useful, but they do not replace a real usage test when one is practical.

### Evidence Format Decision

Do not generate a PDF report by default. For easy results, report the real evidence in a few concise chat lines: command or tool used, real output, and why it passes.

Generate a PDF/report artifact only when:

- the user explicitly asks for a PDF, downloadable report, or artifact
- evidence is long, table-heavy, multi-case, or easier to scan as structured rows
- the output is visual, document-like, image-based, UI-based, or needs side-by-side comparison
- screenshots, rendered pages, before/after images, or document previews need to be reviewed together
- a repo or project rule asks for a report artifact

If a PDF is warranted, use the bundled manifest/report generator:

```bash
python3 scripts/generate_test_pdf_report.py --input /path/to/manifest.json --output /path/to/report.pdf --cleanup-root /path/to/report-cache-root
```

Read `references/report-manifest.md` when building a manifest. The generator rejects passing cases that do not include real `Input`, `Used`, `Output`, and `Why Pass` evidence, or whose output is only a bare status word such as `OK`, `PASS`, `done`, or `works`.

### Report Layout

Choose the report shape from the evidence:

- Code/API/CLI: compact summary table, real command/input/output, key logs, and status.
- UI/browser: screenshots, layout notes, interaction results, and console/runtime evidence.
- Image/edit/generation: before/after or input/output images with readable labels.
- Document/PDF/spreadsheet/slides: rendered page previews and file paths.
- Comparison/audit: expected vs actual tables with visible pass/fail cells.
- Mixed workflows: combine the smallest layout that makes the result reviewable.

For PDF tables, use adaptive full-page layout. Render preview pages and reject unreadably small text, excessive blank space, clipped text, or wildly inconsistent table scale between pages.

## Functional Result And Regression Verification

Use this route when the user asks whether a workflow, code change, optimization, generated output, browser flow, or local process works correctly, still works, produces the same effect as before, or preserves existing behavior.

1. Extract the outcome contract from the user's request and background knowledge: purpose, real input, expected output, preserved behavior, accepted differences, and explicit non-goals.
2. Find the strongest practical baseline: existing tests, before/after screenshots, golden files, saved examples, prior outputs, git-visible behavior, logs, user-supplied references, or documented behavior. Prefer a real baseline over memory.
3. Define pass/fail criteria for the observable effect, not just internal implementation. Include side effects, output location, data shape, user-visible state, error behavior, and any compatibility or regression target the user cares about.
4. Run executable proof when code, scripts, browser flows, or automations are involved. The proof must exercise the changed path with concrete inputs.
5. Compare observed output to the target and baseline. Mark intentional differences as pass only when they are requested or necessary for the goal.
6. State unverified scope explicitly when the baseline is unavailable, private, too expensive, or blocked by missing access.

## Visual And UI Verification

Use this route for UI/UX review, visual QA, responsive layout checks, frontend polish, website/app screens, dashboards, Unity Editor UI, inspector panels, browser views, generated images, game screens, documents, reports, slides, PDFs, typography, spacing, hierarchy, copy, buttons, forms, cards, or user-reported visual problems.

### Required Sources

1. Read `references/visual-verification-rubric.md` for visual checks, then apply only the artifact sections that match the user's output.
2. For UI, websites, app screens, dashboards, editor panels, or browser views, search `references/ui-problem-index.md` by component, symptom, and requested action.
3. For landing pages, portfolios, marketing pages, visual taste reviews, and existing website/app redesigns, fetch or update `leonxlnx/taste-skill` into the current task or project `cache/` folder, never into a random directory:

   ```bash
   mkdir -p cache
   git clone --depth 1 https://github.com/leonxlnx/taste-skill.git cache/taste-skill
   ```

   If it already exists, update it with `git fetch --depth 1 origin` or replace only that cache copy.
4. Read the relevant Taste Skill files before those web/landing/redesign checks:
   - `skills/taste-skill/SKILL.md` for landing pages, portfolios, marketing pages, redesigns, visual taste, layout discipline, and final pre-flight.
   - `skills/redesign-skill/SKILL.md` for existing project upgrades and audit-first redesigns.
   - A more specific Taste Skill variant only when the user's UI type clearly matches it.
5. Do not apply Taste Skill's marketing-page rules to games, documents, dense dashboards, reports, slides, or technical tools except for the general principle of reading the brief before judging aesthetics.

### Visual Check Procedure

1. Capture or open the real visual state first: screenshot, browser target, local app, Unity Editor view, gameplay capture, rendered document page, PDF preview, slide export, generated image, or supplied image.
2. Infer the visual brief from the user: audience, domain, artifact type, brand/style references, platform, constraints, intended mood, and whether beauty, clarity, fidelity, or gameplay/document usability matters most.
3. Select the matching visual rubric section and any matching local problem-index rules. Apply Taste Skill only for the web/landing/redesign cases listed above.
4. Verify the relevant states and sizes. For browser UI, include desktop and narrow/mobile widths when practical. For games, include gameplay-scale readability and at least one real play or motion state when practical. For documents/PDFs/slides, render representative pages or exported slides.
5. Treat clipped text, overlapping controls, unreadable contrast, fake evidence, broken responsive layout, incorrect artifact-specific standard, and missing real visual evidence as blockers unless the user explicitly accepts them.

### Visual Output

State the visual verdict as pass, warning, or fail. Include the user's visual context used, artifact-specific standard, screenshots/previews and sizes, Taste Skill source used when applicable, local index entries used, observed state, and the concrete reason for any blocker. If the visual result passes, explain why the rendered state satisfies the user's requested outcome for that artifact type.

## Local Script And Process Verification

Use this route when the user asks to optimize a repeated workflow into a local script, improve a local automation, validate a helper script, or confirm that a process has become runnable.

1. Read the script and identify its real entry point, inputs, outputs, side effects, and failure modes.
2. Generate small concrete test inputs inside the appropriate `cache/` folder.
3. Run the script exactly as a user would run it.
4. Check these minimums:
   - the script accepts the expected arguments or config
   - the real output matches the requested workflow
   - intermediate/cache files stay in the correct `cache/` folder
   - final files go only to the requested output path
   - rerunning does not corrupt prior outputs
   - errors are clear and non-destructive
   - secrets, auth files, and unrelated user files are not read or written
5. If the workflow is too broad for one check, test the smallest real happy path plus one realistic failure path.

## Skill Or Instruction Verification

Use this route for skill edits, prompt workflows, routing rules, and instruction-layer changes.

- Confirm `SKILL.md` frontmatter has only `name` and `description`.
- Confirm the trigger description matches the user's intended use.
- Confirm referenced files, scripts, and paths exist.
- Confirm old names, deleted skills, or stale references are absent when a rename or deletion was requested.
- Run a small real scenario showing the new route would be selected or the bundled script/resource can run.

## Generated Artifact Verification

Use this route for generated documents, reports, images, PDFs, markdown, data files, or exports.

- Confirm the artifact exists at the intended final path.
- Open, render, parse, or inspect the artifact with the strongest practical local tool.
- Check the artifact against the user's requested content, format, and naming.
- If the artifact has a visual reading surface, combine this route with Visual And UI Verification and read `references/visual-verification-rubric.md`.
- For PDF reports, verify that each passing case contains real input, used method, real output, and a pass reason; fail the report review if it only says `OK`, `PASS`, or `done`.
- For PDF reports with tables, render representative pages and reject unreadably small text, oversized rows, clipped cells, sparse pages where a small table sits at the top, or inconsistent table scale across continuation pages. The table should adapt font size, row height, page size, orientation, and splits to maximize useful page area while staying readable.
- Keep raw generation inputs and review logs in `cache/`; keep final deliverables in the requested location or `outputs/`.

## Relationship To Optimization Skill

`verify-skill` must pass before optional post-task optimization begins, unless the user explicitly asked for optimization as the primary task. After `optimization-skill` changes a script, workflow, skill, reference, or prompt, return to `verify-skill` and prove the optimized path preserves the same observable behavior while reducing repeated work or token load.

## Verification

After editing this skill:

1. Run `optimization-skill`'s targeted validator for `/Users/qin/.codex/skills/verify-skill` and confirm it reports `Verification Passed`.
2. Run a representative contract or scenario check that proves any new verification rule appears in `SKILL.md` and `agents/openai.yaml`.
3. For Obsidian regression-sweep changes, search a real project memory example and confirm that all relevant repeated or prior fixed/corrected issues become checklist items, an under-evidenced current artifact fails, and the retry receives a complete avoidance brief.
4. When publishing, run the management-skill global sync route so public-safety checks happen before push.

## Guardrails

- Do not treat taste as personal preference when a concrete UI rule, screenshot, or external taste-skill pre-flight applies.
- Do not judge all visuals with one generic web-design standard. Use the user's background and the artifact-specific rubric first.
- Do not claim completion from a mock-only, import-only, signature-only, method-parameter-only, or lint-only check when a real local usage check is practical.
- Do not replace the default mini real test with fake, shallow, status-only, compile-only, import-only, route-listing-only, or mock-only checks when a real edited-path test is practical.
- Do not generate a passing PDF that lacks real `Input`, `Used`, `Output`, and `Why Pass` evidence for each passing case.
- Do not use UI screenshots edited by hand as proof that the live UI is fixed.
- Do not verify a local script by reading it only; run it with concrete inputs when possible.
- Do not leave generated verification inputs outside `cache/`.
- Do not hide warnings. A warning is acceptable only when the exact remaining uncertainty is stated.
- Do not pass verification while any applicable item from the Obsidian Regression Sweep remains untested, failed, or unaddressed.
- Do not block the user-facing result on post-pass DailyLog, wiki, Obsidian, Markdown, optimization notes, or other secondary closeout after verification has passed.
- Do not loop forever. Prefer two to three meaningful repair routes, then stop with the exact blocker if the remaining issue requires user action.
- Do not use private credentials, production writes, account switching, payment, or destructive actions as a repair route unless the user explicitly approves that route.
- Do not turn an infeasible task into a fake pass. If the blocker is missing token/access or a logical contradiction, terminate verification and ask for the missing condition.

## Examples

- "Check whether this UI is acceptable" -> use the visual route, visual rubric, Taste Skill when relevant, local problem index, and real screenshots.
- "Verify the game screen looks good" -> use the visual rubric's game section, inspect gameplay-scale readability and motion/gameplay evidence, and do not use marketing-page standards as the main bar.
- "Verify this generated document looks professional" -> render the document/PDF/slides, use the visual rubric's document section, and check readability, hierarchy, page fit, tables, and brand consistency.
- "Verify this optimized script still works" -> run the script with concrete cache inputs and inspect real outputs.
- "Audit this generated PDF report" -> parse or render the PDF and check the required evidence rows.
- "Fix this Python function" -> run a concrete input through the changed function, capture output, compare to expected behavior, and summarize command/output/pass reason in chat unless report evidence is warranted.
- "Give me a QA report" -> run the real workflow first, choose chat/Markdown/PDF by evidence complexity, and generate a PDF only when visual, table-heavy, long, or explicitly requested.
- "Verify this browser flow but login fails" -> inspect console/network/history, try safe alternate browser or local fixture routes, then stop only if private credentials or user approval are required.

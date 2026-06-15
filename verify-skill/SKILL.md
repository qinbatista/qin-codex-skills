---
name: verify-skill
description: "Executor skill under workflow-skill for verification. Use after workflow-skill routes work into checking whether workflows, local scripts, UI/UX, generated artifacts, skill edits, and process optimizations actually satisfy the user's requirement. Use when Codex is asked to verify, review, audit, validate, inspect quality, confirm a workflow, check UI/visual quality, validate that an optimized local script/process still works, or decide whether a failure is fixable. When verification fails, classify feasibility, try safe alternative repair routes before failing, and stop only for logical impossibility or missing user-controlled access such as tokens or private credentials. For UI verification, fetch/read leonxlnx/taste-skill and combine it with the local UI problem index before deciding whether the UI passes. Its verification routes are multi-select: combine every route needed by the artifact."
---

# Verify Skill

Use this as the verification executor selected by `workflow-skill`. It decides what must be checked, what evidence is needed, and which specialized reference should be loaded before accepting work as correct.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

This skill is a verification router with multiple routes. Do not run every route for every task. Select every route that matches the artifact and requested outcome, and combine routes when the request spans UI, local script/process, code behavior, skill/instruction, generated artifact, document/report, or mixed work. Load only the relevant reference files and specialized checks for those routes.

## Trigger

Use this skill when the task is about correctness, quality, audit, validation, UI review, artifact review, or confirming that a finished workflow meets the user's stated target. Do not use this as the primary optimization skill; use `optimization-skill` first for converting repeated workflows into local resources, then use this skill to verify the result.

## Core Rule

Verify the user's actual outcome, not just the method. A check is only useful when it answers: "Does the thing now work, look, read, or behave the way the user asked?"

- Prefer real artifacts, real screenshots, real command output, real files, real browser states, and real run logs.
- Do not call something verified only because code compiles, a method accepts arguments, or a file exists.
- If the task produced code, route the real execution and PDF evidence through `test-skill` after this skill defines the verification criteria.
- Verification PDFs must list the real `Input`, `Used`, `Output`, and `Why Pass` for every passing case. A green status, `OK`, `PASS`, or method name alone is not evidence.
- If the task produced UI, run the UI verification route below before calling the UI acceptable.

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

1. Identify the user's requested outcome and the artifact that should prove it.
2. Classify the verification type: UI, local script/process, code behavior, skill/instruction, generated file, document/report, or mixed.
3. Load only the reference needed for that type.
4. Build a concrete check with real input, real output, and pass/fail criteria.
5. Run or inspect the actual artifact, not a mock substitute, when local execution is practical.
6. If the check fails, run the Feasibility And Repair Loop before returning a fail verdict.
7. Record what was given, what tool/command/workflow was used, what came back, and why that output satisfies, fails, or remains blocked.
8. If the check fails and a fix is in scope, fix the artifact and verify again.
9. Report what passed, what failed, what was attempted, what remains unverified, and where the evidence lives.

## UI Verification

Use this route for UI/UX review, visual QA, responsive layout checks, frontend polish, website/app screens, dashboards, Unity Editor UI, inspector panels, browser views, typography, spacing, hierarchy, copy, buttons, forms, cards, or user-reported UI problems.

### Required Sources

1. Search `references/ui-problem-index.md` first by component, symptom, and requested action.
2. Fetch or update `leonxlnx/taste-skill` into the current task or project `cache/` folder, never into a random directory:

   ```bash
   mkdir -p cache/taste-skill
   git clone --depth 1 https://github.com/leonxlnx/taste-skill.git cache/taste-skill
   ```

   If it already exists, update it with `git fetch --depth 1 origin` or replace only that cache copy.
3. Read the relevant Taste Skill files before UI verification:
   - `skills/taste-skill/SKILL.md` for landing pages, portfolios, marketing pages, redesigns, visual taste, layout discipline, and final pre-flight.
   - `skills/redesign-skill/SKILL.md` for existing project upgrades and audit-first redesigns.
   - A more specific Taste Skill variant only when the user's UI type clearly matches it.

### UI Check Procedure

1. Capture or open the real UI state first: screenshot, browser target, local app, Unity Editor view, or supplied image.
2. Apply matching local problem-index rules.
3. Apply Taste Skill's relevant pre-flight checks, especially redesign audit, one design system, real images, contrast, CTA wrapping, hero fit, navigation line fit, mobile collapse, copy self-audit, and no generic AI layout tells.
4. Verify at the relevant breakpoints. For browser UI, include desktop and narrow/mobile widths when practical.
5. Treat clipped text, wrapped compact controls, unreadable contrast, fake screenshots, broken responsive layout, and missing real evidence as blockers unless the user explicitly accepts them.

### UI Output

State the UI verdict as pass, warning, or fail. Include the screenshots, viewport sizes, Taste Skill source used, local index entries used, observed page state, and the concrete reason for any blocker. If the UI passes, explain why the screenshots/page state satisfy the user's requested outcome.

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
- For PDF reports, verify that each passing case contains real input, used method, real output, and a pass reason; fail the report review if it only says `OK`, `PASS`, or `done`.
- Keep raw generation inputs and review logs in `cache/`; keep final deliverables in the requested location or `outputs/`.

## Relationship To Test Skill

`verify-skill` decides what correctness means and which reference rules apply. `test-skill` executes real tests and generates PDF evidence after code changes, scripted workflows, or report-worthy validation. Use both when a task needs verification criteria plus executable proof.

## Guardrails

- Do not treat taste as personal preference when a concrete UI rule, screenshot, or external taste-skill pre-flight applies.
- Do not use UI screenshots edited by hand as proof that the live UI is fixed.
- Do not verify a local script by reading it only; run it with concrete inputs when possible.
- Do not leave generated verification inputs outside `cache/`.
- Do not hide warnings. A warning is acceptable only when the exact remaining uncertainty is stated.
- Do not loop forever. Prefer two to three meaningful repair routes, then stop with the exact blocker if the remaining issue requires user action.
- Do not use private credentials, production writes, account switching, payment, or destructive actions as a repair route unless the user explicitly approves that route.
- Do not turn an infeasible task into a fake pass. If the blocker is missing token/access or a logical contradiction, terminate verification and ask for the missing condition.

## Examples

- "Check whether this UI is acceptable" -> use the UI route, Taste Skill, local problem index, and real screenshots.
- "Verify this optimized script still works" -> run the script with concrete cache inputs and inspect real outputs.
- "Audit this generated PDF report" -> parse or render the PDF and check the required evidence rows.
- "Verify this browser flow but login fails" -> inspect console/network/history, try safe alternate browser or local fixture routes, then stop only if private credentials or user approval are required.

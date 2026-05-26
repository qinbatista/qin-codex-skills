---
name: qin-done-means-tested
description: Mandatory final verification skill. Use for any coding, website, UI, script, automation, refactor, bug fix, content update, or file-edit task before claiming the work is done. Always run the most relevant test, preview, build, lint, screenshot, or validation step available, and clearly report what was tested or what could not be tested.
---

# Qin Done Means Tested

Do not finish a task just because the edits are written.

Before the final response, run the strongest practical verification that fits the task.

## Trigger

Use this skill whenever work changed code, content, UI, configuration, scripts, automation, or generated output and you are about to say the task is done.

## Workflow

1. Identify the most relevant validation step for the work.
2. Run it before claiming completion.
3. If the first check fails, fix the issue and test again when practical.
4. If testing is blocked, say exactly why it was blocked and what remains unverified.
5. If real or repeated testing shows unstable output, failures, or partially correct behavior, say it is not fully fixed yet and include the concrete pass/fail evidence instead of claiming completion.
6. After Chrome-backed testing, close or finalize Chrome tabs/windows opened or claimed only for that test. If no other browser task, user handoff, login, approval, download, or requested open page still needs Chrome, close the Chrome app too; otherwise leave Chrome running and state what kept it open.
7. The user's standing preference is to always push completed code after clean testing. After tests pass with no remaining problem, commit and push the completed task-related code to `main` by default when the work is in a git repo with a configured remote, unless the user explicitly says not to push or a closer repo-specific workflow gives a different target/sequence. Before every push, pull or otherwise fetch and integrate the latest remote code for the target branch using the repo's normal workflow. If conflicts appear, inspect why each conflict happened, merge the code deliberately so both local task intent and remote intent are preserved where compatible, rerun the relevant checks after the merge, then push only after the resolved merge is saved. Unrelated dirty files are not a reason to skip pushing: stage only the files for the completed task, preserve unrelated dirty work, and report if committing or pushing is blocked.

## Validation rules

- For website or UI work:
  Run a local preview when possible.
  Hard rule: after the work is done, capture a full-page rendered image review and show that full-page preview in the final response whenever the surface can be rendered as a page or screen.
  A component crop, viewport crop, or PDF preview may be included as extra evidence, but it does not replace the full-page image preview for page-like UI work.
  If a full-page image is not practical, state the concrete blocker and show the widest useful rendered screenshot instead.
  Capture at least one desktop check.
  Capture at least one mobile or narrow-screen check when the layout is responsive.
  Treat desktop and narrow-screen checks as both required when responsive behavior changed.
  Look for alignment, overflow, unreadable text, missing images, broken spacing, and wrapped labels inside mobile nav, CTA, pill, chip, or other compact controls.
  If mobile control text wraps, the verification has not passed yet. Shorten the label or switch to a folded menu/control pattern and test again.
  In the final response, include the full-page rendered image preview when practical so the user can review the whole result immediately.

- For frontend or app code:
  Prefer targeted build, lint, test, or browser verification over no-op checks.

- For backend, scripts, or CLI changes:
  Run the narrowest relevant test command, sample execution, or syntax check that proves the change works.

- For skill updates:
  After editing a `SKILL.md`, skill script, prompt, or instruction workflow, run the narrowest small working test that exercises the updated behavior. If it fails, keep updating and rerunning the test until it passes or a concrete blocker remains.

- For content-only edits:
  Verify the rendered output or resulting file where possible instead of only reading the source.

- For Unity Editor, Unity UI, or Unity asset-generation work:
  Verify in the live Unity Editor when the behavior depends on editor rendering, inspector controls, custom editor windows, generated previews, or asset import results. Always include the Unity test evidence in the final response, preferably a screenshot or comparison image from the actual Unity window plus the relevant compile/log check. If Unity is stuck, missing, unresponsive, or the window cannot be inspected, reopen or restart Unity and rerun the verification before claiming the work is done. If Unity still cannot be recovered, report the concrete blocker and do not claim the Unity behavior is fixed.

- For Chrome-backed tests:
  Treat cleanup as part of being done. Use the available Chrome/browser cleanup path to release or close test-only tabs, then close Chrome itself when it is safe because no other task is still running in Chrome. Do not close user-owned tabs, active handoff pages, login/approval pages, or requested deliverables.

## Final response rules

- State what you tested.
- State the result.
- For Unity work, show the Unity test evidence every time when it exists, including the screenshot/comparison path or rendered image and the compile/log status.
- For website, UI, image, visual, document-preview, or generated-output tasks, include the three-part handoff whenever the artifacts exist: rendered image evidence, a concise report of what changed and what passed, and the live preview URL or local file/path to open. If one of the three is unavailable, say exactly which artifact is missing and why instead of omitting it silently.
- When the user asks whether the issue is fixed, answer directly from the test evidence.
- If something was not tested, say that plainly.
- Do not imply full verification when only partial checks were run.
- For website or UI tasks, show the full-page rendered image preview in the final response when practical; if only a crop is shown, explain why the full page could not be captured.
- If the user explicitly asked for testing, QA, validation, a smoke test, a regression pass, a test report, a PDF report, a visual report, a review report, an audit report, evidence output, or a result artifact, pair this skill with `/Users/qin/.codex/skills/qin-test-pdf-report/SKILL.md` and deliver the result as a PDF report rather than a text-only recap.

## Guardrails

- Do not skip verification just because the change looks small.
- Do not claim full success from lint-only or syntax-only checks when runtime behavior changed materially.
- Do not hide blocked or partial verification behind vague wording.
- Do not replace a requested PDF report with a plain chat recap.

## Examples

- "I fixed the Python script." -> run the narrowest useful script or test before finishing.
- "Check this UI change." -> verify visually and include a screenshot when practical.
- "Give me a PDF report for this QA pass." -> pair with `qin-test-pdf-report` and return the PDF path.

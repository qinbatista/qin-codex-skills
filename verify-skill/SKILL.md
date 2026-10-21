---
name: verify-skill
description: "Verify consequential changes inside the active task with the smallest check that demonstrates the requested behavior."
---

# Verify

Before any verification write, apply the [external artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Screenshots, JSON receipts, logs, fixtures, results and tool caches stay in the isolated external task directory from their first write. Maintained regression tests keep their source owner; inspect exact paths and the Git index before committing.

Verify before declaring the task complete. Follow [Task Analyze's action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests) when checks fail or cannot run. Read relevant project facts through Project Memory, skip absent matching records, and never borrow another project's facts.

## Project testing Skill and test levels

For an identifiable project, before creating a maintained Python test file or starting an extended test campaign, inspect the project's `.agents/skills` and existing test owners for an applicable testing Skill. Read and follow it when present; if none covers the project, create `.agents/skills/testing-skill` before adding maintained tests. Give that Skill a concise, stable map of each test purpose and goal, test level, project-relative script path, runner, and required file owner. Refresh the map when tests change. Prefer its non-runtime `tests/` for new maintained scripts. Keep tests that a toolchain or release gate requires elsewhere, such as Unity tests or a Skill's own clean-clone tests, at their required paths and track them in the map. Do not duplicate them in the testing Skill.

Select the smallest level that can prove the claim: level 1 checks a focused function and syntax/code errors; level 2 exercises the affected case in its real runtime and is the default; level 3 exercises all related code when a structural change can affect multiple paths; level 4 is full-system or release validation only when explicitly requested or required by the actual release contract. Level 1 alone does not establish consequential behavior. Audit the map and existing cases by *purpose* before adding a script or widening a run: update or combine useful cases, remove obsolete exact duplicates after updating references, and retain distinct compatibility or release-gate coverage. Keep outcomes, temporary fixtures and runner caches in the isolated external task owner, not in the stable testing Skill or project directories.

## Choose evidence

- API checks, client tests, and push/release tests default to process and workflow acceptance: verify request/response contracts, job completion, save/reopen when applicable, generated artifact existence, successful downloads, and valid file bytes. For images, check that output was generated and can be decoded; do not compare artwork, garment details, text, colors, or other content with the source. For documents, check generation, delivery, format, and required files/pages; do not judge content or visual quality. Do not pause these tests or block a push because of an unsolicited quality assessment. Add image/content quality, source fidelity, or layout review only when the user explicitly requests that scope. Keep intrinsic production checks unchanged, preserve their actual statuses, and report quality as not assessed when it was not requested.
- Simple code edits: read back the changed value and exercise the affected consumer when one exists.
- Logic or structural changes: exercise changed behavior with focused existing tests or a small isolated case, including the important failure boundary.
- UI/layout creation, repair, or explicitly requested visual review: apply the [shared readable UI rules](../workflow-skill/references/readable-ui.md). Inspect web layouts at desktop and narrow widths; render affected PDF/report pages and slides at their intended reading size. Check containment, alignment, typography, and useful density. Exercise interactions only where they exist. Source review alone cannot prove appearance. Ordinary API/client/release workflow tests do not trigger this visual-quality gate.
- Data, scripts, APIs, and installation: use a bounded real input, output readback, or state query that proves the promised result.

Use one real verification path: execute the changed behavior or inspect the actual output. A syntax check, mock, or quick smoke test may help diagnose a failure, but cannot replace evidence for the promised behavior. Prefer existing runtimes and focused checks. Do not start the whole application, compile the whole project, launch Unity, run every test, or incur external costs unless requested. If only a broader unauthorized action resolves uncertainty, complete the authorized implementation and available focused checks first, then report the specific verification gap alongside the delivered changes without claiming unverified behavior.

For browser-based verification, read and apply [Workflow's browser testing policy](../workflow-skill/SKILL.md#browser-testing).

Use [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md): hide every test subprocess, use native headless rendering, and capture output without opening or activating windows. Preserve supported platform branches and report which were actually tested.

## Bind evidence to the actual target

Before a consequential check, identify the actual consumer and the result being claimed. Bind evidence to the relevant source revision or content hash, served process or installed artifact, effective configuration, runtime/ABI, and provider/environment. Record only the identifiers material to the claim; do not expose secrets or build a new reporting system. Confirm which workspace and version a running service actually loaded before treating a successful response as proof of the edited source.

Keep these boundaries explicit:

- Source review or a matching hash establishes source identity. A passing mock or synthetic fixture establishes only the modeled contract; runtime behavior needs the real affected consumer.
- A browser, Editor, desktop Player, emulator, Simulator, physical device, store package, and provider backend are distinct surfaces. Run the supported available checks and report remaining surfaces separately; never promote one to evidence for another.
- Build/export success, local installation, submission accepted, backend completion, and provider acceptance are separate outcomes. A dispatched callback or HTTP request does not prove the remote side effect completed. Read the authoritative resulting state when that completion is the claim.
- For configuration or artifact changes, read the effective values and delivered bytes through the final consumer. An old log, cached preview, receipt from another build, or filename alone cannot identify this result.

Choose a relevant failure or ordering boundary when it can invalidate the fix, following [state and side effects](../code-skill/references/state-and-side-effects.md). Report observed results and pending limits separately; do not rerun unrelated systems or upgrade historical evidence merely to fill a checklist.

## Finish

Map requirements to existing evidence before adding checks. Audit existing tests when behavior or goals change: remove obsolete or duplicate cases, update a useful case before adding a new file, and keep only coverage for a current behavior or deliberate compatibility boundary. Put retained tests in the project location specified by the [Cache and test placement policy](../workflow-skill/references/project-cache-artifact-policy.md); execute moved tests from their final path. Add a case only for an uncovered requirement or observed failure. Fix failures here, then rerun only affected checks. After a style-check failure, rerun that check for a formatting-only fix; leave unaffected behavior checks alone. Stop when relevant checks and visual review pass; do not add overlapping tests or repeat unaffected checks. Verify final bytes and updated references in their declared durable owner through a fresh consumer, then close unused task-opened surfaces and delete disposable verification files, test/build intermediates and empty task directories. Preserve useful user review/reuse files and live environments until their backing owner/references are verified; paused or failed work keeps minimum recovery inputs/state and cleans independent disposable work under the [resource lifecycle](../workflow-skill/references/task-resource-lifecycle.md). Report compact pass counts, failures, skips, cleanup, and limitations instead of dumping successful reports.

Ending uses [Project Memory](../project-memory-skill/SKILL.md) for facts established here and runs [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md) in parallel. It preserves active work and user review/reuse, releases confirmed disposable completed-task resources, and never re-verifies, repairs code or changes this task's result. Historical Ending plans must not execute old product check commands.

The optional `scripts/task_verification.py` helper selects bounded verification scope. Report helpers remain available for explicitly requested visual/PDF reports.

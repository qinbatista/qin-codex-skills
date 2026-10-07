---
name: verify-skill
description: "Verify consequential changes inside the active task with the smallest check that demonstrates the requested behavior."
---

# Verify

Before any file write for verification, apply the [Cache policy](../workflow-skill/references/project-cache-artifact-policy.md). Temporary screenshots, JSON receipts, logs, fixtures, and test output go only in ignored `Cache/temp-<task>/` from their first write. Maintained regression tests keep their source owner. Inspect exact paths and the Git index before staging or committing; temporary files never enter Git.

Verify before declaring the task complete. Follow [Task Analyze's action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests) when checks fail or cannot run. Read relevant project facts through Project Memory, skip absent matching records, and never borrow another project's facts.

## Project testing Skill and test levels

For an identifiable project, before creating a maintained Python test file or starting an extended test campaign, inspect the project's `.agents/skills` and existing test owners for an applicable testing Skill. Read and follow it when present; if none covers the project, create `.agents/skills/testing-skill` before adding maintained tests. Give that Skill a concise, stable map of each test purpose and goal, test level, project-relative script path, runner, and required file owner. Refresh the map when tests change. Prefer its non-runtime `tests/` for new maintained scripts. Keep tests that a toolchain or release gate requires elsewhere, such as Unity tests or a Skill's own clean-clone tests, at their required paths and track them in the map. Do not duplicate them in the testing Skill.

Select the smallest level that can prove the claim: level 1 checks a focused function and syntax/code errors; level 2 exercises the affected case in its real runtime and is the default; level 3 exercises all related code when a structural change can affect multiple paths; level 4 is full-system or release validation only when explicitly requested or required by the actual release contract. Level 1 alone does not establish consequential behavior. Audit the map and existing cases by *purpose* before adding a script or widening a run: update or combine useful cases, remove obsolete exact duplicates after updating references, and retain distinct compatibility or release-gate coverage. Keep outcomes and temporary fixtures in task-owned Cache, not in the stable testing Skill.

## Choose evidence

- Simple code edits: read back the changed value and exercise the affected consumer when one exists.
- Logic or structural changes: exercise changed behavior with focused existing tests or a small isolated case, including the important failure boundary.
- UI and visual presentation: apply the [shared readable UI rules](../workflow-skill/references/readable-ui.md). Inspect web layouts at desktop and narrow widths; render affected PDF/report pages and slides at their intended reading size. Check containment, alignment, typography, and useful density. Exercise interactions only where they exist. Source review alone cannot prove appearance.
- Data, scripts, APIs, and installation: use a bounded real input, output readback, or state query that proves the promised result.

Use one real verification path: execute the changed behavior or inspect the actual output. A syntax check, mock, or quick smoke test may help diagnose a failure, but cannot replace evidence for the promised behavior. Prefer existing runtimes and focused checks. Do not start the whole application, compile the whole project, launch Unity, run every test, or incur external costs unless requested. If only a broader unauthorized action resolves uncertainty, complete the authorized implementation and available focused checks first, then report the specific verification gap alongside the delivered changes without claiming unverified behavior.

For any browser-based verification, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence.

Use [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md): hide every test subprocess, use native headless rendering, and capture output without opening or activating windows. Preserve supported platform branches and report which were actually tested.

## Finish

Map requirements to existing evidence before adding checks. Audit existing tests when behavior or goals change: remove obsolete or duplicate cases, update a useful case before adding a new file, and keep only coverage for a current behavior or deliberate compatibility boundary. Put retained tests in the project location specified by the [Cache and test placement policy](../workflow-skill/references/project-cache-artifact-policy.md); execute moved tests from their final path. Add a case only for an uncovered requirement or observed failure. Fix failures here, then rerun only affected checks. After a style-check failure, rerun that check for a formatting-only fix; leave unaffected behavior checks alone. Stop when relevant checks and visual review pass; do not add overlapping tests or repeat unaffected checks. Verify final bytes and updated references in their declared durable owner through a fresh consumer, then close unused task-opened surfaces and delete disposable verification files, test/build intermediates and empty task directories. Preserve useful user review/reuse files and live environments until their backing owner/references are verified; paused or failed work keeps minimum recovery inputs/state and cleans independent disposable work under the [resource lifecycle](../workflow-skill/references/task-resource-lifecycle.md). Report compact pass counts, failures, skips, cleanup, and limitations instead of dumping successful reports.

Ending uses [Project Memory](../project-memory-skill/SKILL.md) for facts established here and runs [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md) in parallel. It preserves active work and user review/reuse, releases confirmed disposable completed-task resources, and never re-verifies, repairs code or changes this task's result. Historical Ending plans must not execute old product check commands.

The optional `scripts/task_verification.py` helper selects bounded verification scope. Report helpers remain available for explicitly requested visual/PDF reports.

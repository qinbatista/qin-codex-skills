---
name: verify-skill
description: "Verify consequential changes inside the active task with the smallest check that demonstrates the requested behavior."
---

# Verify

Verify before declaring the task complete. Keep the user's selected model and effort when skills govern the work. Read relevant project memory if present; skip missing memory and never borrow another project's facts.

## Choose evidence

- Simple code edits: read back the changed value and exercise the affected consumer when one exists.
- Logic or structural changes: exercise changed behavior with focused existing tests or a small isolated case, including the important failure boundary.
- UI and visual presentation: apply the [shared readable UI rules](../workflow-skill/references/readable-ui.md). Inspect web layouts at desktop and narrow widths; render affected PDF/report pages and slides at their intended reading size. Check containment, alignment, typography, and useful density. Exercise interactions only where they exist. Source review alone cannot prove appearance.
- Data, scripts, APIs, and installation: use a bounded real input, output readback, or state query that proves the promised result.

Use one real verification path: execute the changed behavior or inspect the actual output. A syntax check, mock, or quick smoke test may help diagnose a failure, but cannot replace evidence for the promised behavior. Prefer existing runtimes and focused checks. Do not start the whole application, compile the whole project, launch Unity, run every test, or incur external costs unless requested. If only a broader action resolves uncertainty, report the gap instead of claiming success.

For any browser-based verification, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence.

Use [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md): hide every test subprocess, use native headless rendering, and capture output without opening or activating windows. Preserve supported platform branches and report which were actually tested.

## Finish

Map requirements to existing evidence before adding checks. Audit existing tests when behavior or goals change: remove obsolete or duplicate cases, update a useful case before adding a new file, and keep only coverage for a current behavior or deliberate compatibility boundary. Put retained tests in the project location specified by the [Cache and test placement policy](../workflow-skill/references/project-cache-artifact-policy.md); execute moved tests from their final path. Add a case only for an uncovered requirement or observed failure. Fix failures here, then rerun only affected checks. After a style-check failure, rerun that check for a formatting-only fix; leave unaffected behavior checks alone. Stop when relevant checks and visual review pass; do not add overlapping tests or repeat unaffected checks. After readback, close task-opened review surfaces and remove task-owned temporary verification files unless the user still needs to review them or debugging continues. Report compact pass counts, failures, skips and limitations instead of dumping successful reports.

Ending belongs to [Project Memory](../project-memory-skill/SKILL.md) and only updates local memory with facts established here. It never verifies, repairs, or changes this task's result. Historical Ending plans must not execute old check commands.

The optional `scripts/task_verification.py` helper selects bounded verification scope. Report helpers remain available for explicitly requested visual/PDF reports.

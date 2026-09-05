---
name: verify-skill
description: "Verify consequential changes inside the active task with the smallest check that demonstrates the requested behavior."
---

# Verify

Verify before declaring the task complete. Keep the user's selected model and effort when skills govern the work. Read relevant project memory if present; skip missing memory and never borrow another project's facts.

## Choose evidence

- Simple value-only edits: skip verification unless requested or an observed risk warrants a check.
- Logic or structural changes: exercise changed behavior with focused existing tests or a small isolated case, including the important failure boundary.
- UI and visual presentation: apply the [shared readable UI rules](../workflow-skill/references/readable-ui.md). Inspect web layouts at desktop and narrow widths; render affected PDF/report pages and slides at their intended reading size. Check containment, alignment, typography, and useful density. Exercise interactions only where they exist. Source review alone cannot prove appearance.
- Data, scripts, APIs, and installation: use a bounded real input, output readback, or state query that proves the promised result.

Prefer existing runtimes and focused checks. Do not start the whole application, compile the whole project, launch Unity, run every test, or incur external costs unless the user requested that scope. If only a broader action resolves uncertainty, report the gap and ask for that action rather than claiming success.

Use [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md): hide every test subprocess, use native headless rendering, and capture output without opening or activating windows. Preserve supported platform branches and report which were actually tested.

## Finish

Map requirements to existing evidence before adding checks. Use an adequate supplied checker; add a case only for an uncovered requirement or observed failure. Fix failures here, then rerun only affected checks. After a style-check failure, rerun that check for a formatting-only fix; leave unaffected behavior checks alone. Stop when relevant checks and visual review pass; do not add overlapping tests or repeat unaffected checks. Report compact pass counts, failures, skips and limitations instead of dumping successful reports.

Ending belongs to [Project Memory](../project-memory-skill/SKILL.md) and only records useful facts already established here. It never verifies or launches automatic repair tasks. Historical Ending plans must not execute old check commands.

The optional `scripts/task_verification.py` helper selects bounded verification scope. Report helpers remain available for explicitly requested visual/PDF reports.

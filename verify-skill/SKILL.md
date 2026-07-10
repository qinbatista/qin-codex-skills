---
name: verify-skill
description: "Use when the locked task-analyze-skill plan needs Mini Verify, Real Verify, QA, tests, UI/visual review, artifact inspection, regression, or optimization proof. Mini Verify is the proportional gate before the first result. Real Verify runs after that result in background Ending Task. A Real failure notifies and reopens. Optimization requires a verifier different from its implementer."
---

# Verify Skill

Use this as the verification executor named by the locked `task-analyze-skill` plan and coordinated by `workflow-skill`. Follow each verification node's exact model, effort, dependencies, input, output, and stop condition. Do not move a node across the Main Result boundary or silently change its model.

## First Result Principle

Finish the requested task, run the smallest meaningful Mini Verify, and show the basically verified result immediately. Continue deeper Real Verify, broader regression checks, optimization proof, reports, logs, documentation, and routing learning in Ending Task after the result. If later verification finds a correctness problem, notify the user, reopen the task, repair, rerun Mini Verify, and present the corrected result. Never call Mini Verify exhaustive proof.

## Internal Route Selection

### Two Verification Categories

### Mini Verify

Mini Verify is the only verification gate for the first main result. It is the fastest proportional check that can catch a basic broken result.

Examples:

- reread the changed value or requested answer;
- syntax, compile, import, lint, schema, or file-existence check;
- one focused real input/output check;
- parse a generated document or inspect page/basic content;
- confirm a UI/artifact renders without an obvious error;
- validate skill frontmatter, required files, or a focused routing scenario;
- confirm requested versus resolved model/effort for a model-routing acceptance target.

For topology:

- parallel independent result branches receive branch Mini Verify when merge cannot expose their basic failure;
- sequential work receives one consolidated Mini Verify after the final dependent result step;
- mixed work receives an integration Mini Verify after merge, with branch checks only when needed.

When Mini Verify fails, return the failure to the affected result-bearing node, repair, and rerun. When it passes and the requested work is complete, return `Mini Verify: pass` to Workflow so Main Goal Done Gate can release the result.

Mini Verify proves basic readiness. It does not claim realistic, exhaustive, regression, or production proof.

### Real Verify

Real Verify begins after the main result inside Ending Task. It exercises the actual path with realistic inputs, rendered evidence, interaction, integration, baseline comparison, broader regressions, or live-environment behavior.

Use it for relevant:

- major/shared logic and realistic code paths;
- UI, responsive, interaction, visual, image, PDF, document, or report quality;
- public contracts, integration, browser, deployment, or live runtime behavior;
- broad project/Obsidian regression sweeps;
- prompt behavior across representative cases;
- model-route replay and token/time baselines;
- same-behavior optimization comparison.

Real Verify never blocks the first Mini-verified result. Report its worker/model/effort as running. If Real Verify later finds a correctness failure, notify the user, reopen the task, provide the failing evidence, and route any repair through a new Mini Verify before a corrected result is claimed.

Do not relabel compile/import/existence-only evidence as Real Verify when realistic behavior is practical.

## Model And Receipt Contract

Use the model and effort assigned by Task Analyze:

- Luna normally handles bounded Mini Verify judgment and lightweight records.
- Terra normally handles grounded Real Verify, source-rich comparisons, realistic tests, and integration evidence.
- Sol handles ambiguous, open-ended, or high-complexity judgment.
- Spark may author a probe in an active registry-owned code domain only through `code-skill`; verification judgment remains on the planned verification model.

Runtime model labels are not proof. When routing evidence matters, inspect the sanitized [runtime receipt contract](../task-analyze-skill/references/runtime-receipts.md). Fail a claimed model/effort match when runtime metadata disagrees and no allowed reroute exists.

## Verification Workflow

1. Read the planned verification node and observable pass target.
2. Classify it as Mini Verify or Ending Task Real Verify; never combine their claims.
3. Select the smallest evidence source that can answer that category.
4. Run/inspect the actual artifact or state when practical.
5. Record input, method, observed output, and why pass/fail.
6. For failure, give a concise reproduction and affected result.
7. Return Mini verdicts to `workflow-skill`; return Real verdicts to the Ending Task dispatcher.

## Artifact Routes

### Code And Scripts

- Mini: syntax/compile/basic route plus one focused input/output when proportional.
- Real: realistic edited-path behavior, regression, error semantics, side effects, ordering, performance baseline, or live Unity/runtime evidence.
- Active code-domain probe authoring uses `code-skill` and the planned Spark-first node.

### Skills And Instructions

- Mini: frontmatter, description/agent length, referenced-file existence, syntax, and focused positive/negative contract scenarios.
- Real: loader discovery, live task replay, model/effort receipt, stale-name search, downstream behavior, and mirror snapshot behavior.
- Static wording checks alone do not prove a major routing change.

### UI, Images, And Visual Artifacts

- Mini: real render/open, basic dimensions/state, console/runtime sanity, and obvious target presence.
- Real: inspect desktop and narrow states, interactions, before/after evidence, layout, hierarchy, clipping, readability, consistency, and the user's applicable taste rules.
- Use `references/visual-verification-rubric.md` and `references/ui-problem-index.md` when relevant.

### Documents, PDFs, And Reports

- Mini: parse/open, page count, required sections, basic content, and output path.
- Real: rendered pages, typography, spacing, clipping, tables, visual hierarchy, and source-backed correctness.
- Use `references/report-manifest.md` for formal evidence reports.

### Browser, Computer, Automation, And Deployment

- Mini: expected state/command/URL exists and basic action completed.
- Real: execute the real interaction path, inspect errors and side effects, and confirm final observable state.
- A planned production/public action still needs authorization before execution; that is a safety precondition, not post-result verification.

## Obsidian Regression Sweep

For connected projects, repeated failures, global skills, UI/visual/generated artifacts, browser/deployment, or user-corrected behavior, use relevant Obsidian memory as an Ending Task regression baseline:

1. Read only the directly related memory pages and applicable prior failures.
2. Build a checklist of repeated failures, user corrections, and previously fixed issues in the touched scope.
3. Test each applicable item with concrete evidence.
4. A failure notifies and reopens the task.
5. Save sanitized lessons only; never store secrets or raw private transcripts.

Do not delay the first Mini-verified result for the broader sweep.

## Optimization Verification

Optimization verification is an Ending Task Real Verify route. The verifier must be different from the implementer.

Require:

- optimizer and verifier identities;
- raw before/after inputs and outputs;
- same-behavior comparison;
- token/time measurements when savings are claimed;
- dependency, order, side-effect, and error-semantics checks;
- identical prompts/inputs/acceptance criteria for benchmark claims.

If no different verifier is callable, report `independent optimization verification blocked`; do not self-certify.

## Evidence Output

For concise chat evidence, report:

- `Category`: Mini Verify or Real Verify;
- `Input`;
- `Used`;
- `Output`;
- `Why pass/fail`;
- `Model receipt`, when routing is part of acceptance.

Create a formal report only when the user requests one, the evidence is long/table-heavy/visual/comparison-based, or a repository contract requires it. Every passing report row includes `Input`, `Used`, `Output`, and `Why Pass`.

## Generated File Placement

Put fixtures, logs, screenshots, receipts, parsed data, and previews in the task/project `cache/` or `work/` area. Put final user-facing reports only in the requested location or active workspace `outputs/`.

## Guardrails

- Verify the user's observable result, not only the attempted method.
- Do not hide uncertainty or a blocked environment.
- Do not claim a model ran without runtime evidence.
- Do not let Real Verify block the first Mini-verified result.
- Do not let a Real failure disappear as background noise; notify and reopen.
- Do not let an optimization implementer verify its own behavior.
- Do not push, deploy, or send external messages unless explicitly authorized.

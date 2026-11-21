---
name: verify-skill
description: "Verify consequential changes inside the active task with the smallest check that demonstrates the requested behavior."
---

# Verify

Before verification writes, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Put scratch and tool caches in the isolated run from the first write. Keep maintained tests with their source owner and check exact paths and the Git index before committing.

Verify in the active task. Use scoped Project Memory and skip absent records. Apply [Task Analyze's action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests) when a check fails or cannot run.

## Project testing Skill and test levels

Before adding a maintained Python test or starting extended project testing, look for an applicable testing Skill in the declared project Skill owner and existing test owners. Read it if present. If absent, create `testing-skill` before adding maintained tests, under visible `skills/` for visible-source projects or the existing `.agents/skills` owner. Keep a current map of purpose, goal, level, relative script path, runner and file owner. Prefer its non-runtime `tests/` for new scripts. Map toolchain and release tests, including clean-clone tests, at their required paths as single copies.

Select the smallest level that supports the claim.

1. Focused function or syntax/code-error check. Consequential behavior needs real evidence.
2. Affected case in its actual runtime. Use by default.
3. All related code when a structural change affects multiple paths.
4. Full-system or release validation when explicitly requested or required by the release contract.

Audit tests by purpose before adding coverage or widening a run. Update or combine useful cases and remove obsolete exact duplicates after updating references. Keep distinct compatibility and release coverage.

## Choose evidence

For large logs, use [Workflow's bounded reading](../workflow-skill/references/text-and-log-reading.md). Start at the latest page and trace observed identifiers to their cause.

- API, client and push/release tests default to workflow acceptance. Check contracts, job completion, save/reopen where applicable, artifact generation, downloads and valid bytes. Decode images and check document delivery, format and required files/pages. Keep intrinsic production checks and their actual statuses. Add quality, source fidelity or layout review only at the user's request. Otherwise report quality as unassessed and keep testing or delivery moving.
- Simple code edits: read back the changed value and exercise the affected consumer when one exists.
- Logic or structural changes: exercise the behavior and consequential failure boundary with focused existing tests or a small isolated case.
- UI/layout creation, repair or requested visual review: apply the [shared readable UI rules](../workflow-skill/references/readable-ui.md). Inspect actual renders at desktop and narrow widths for web, or intended reading size for PDFs, reports and slides. Check containment, alignment, typography, density and existing interactions. Ordinary API/client/release workflow tests skip this visual-quality gate.
- Data, scripts, APIs, and installation: use a bounded real input, output readback, or state query that proves the promised result.

Use one real path through the affected behavior or actual output. Use syntax checks, mocks and smoke tests for diagnosis and keep claims within their evidence. Prefer existing runtimes and focused checks. Whole-application startup, full builds, exhaustive tests and external costs require user authorization. If broader verification needs authorization, complete the authorized implementation and available focused checks first, then state the specific evidence gap.

For browser-based verification, read and apply [Workflow's browser testing policy](../workflow-skill/SKILL.md#browser-testing).

Use [portable, quiet execution](../code-skill/references/skill-platform-compatibility.md) for hidden subprocesses, native headless rendering and captured output. Preserve platform branches and report the ones actually tested.

## Bind evidence to the actual target

Identify the consumer and claim. Confirm the workspace and version loaded by a running service. Bind material evidence to the source revision or hash, served process or installed artifact, effective configuration, runtime/ABI and provider/environment. Keep secrets out of evidence and use existing reporting.

- Source review and hashes establish source evidence. Mocks and synthetic fixtures cover modeled contracts. Verify runtime claims through the affected consumer.
- Report the actual surface, whether browser, desktop application, emulator, simulator, physical device, store package or provider backend. Run supported checks and state outstanding surfaces.
- Verify each claimed stage at its owner, from build/export and installation through submission, backend completion and provider acceptance. For remote side effects, read authoritative resulting state after a callback or request.
- Read effective configuration and delivered bytes through the final consumer. Bind any log, preview or receipt to the exact result.

Exercise failure or ordering boundaries that could invalidate the fix under [state and side effects](../code-skill/references/state-and-side-effects.md). Report observed results and pending limits with current evidence.

## Finish

Map requirements to evidence first. Add cases only for an uncovered requirement or observed failure, and run moved tests from their final path. Fix failures here and rerun only affected checks, such as a style check for a formatting-only fix. Stop when relevant checks and required visual review pass.

Read back final bytes and references in their durable owner. Apply [the unit cleanup plan](../workflow-skill/references/project-cache-artifact-policy.md#plan-before-producing-files) after each reported result, closing unused owned surfaces and deleting disposable verification files and intermediates. Preserve only exact necessary inputs or explicit holds. For a pause or failure, keep minimum recovery state and release independent scratch under the [resource lifecycle](../workflow-skill/references/task-resource-lifecycle.md). Report counts, failures, skips, cleanup and limits concisely.

Use [Project Memory](../project-memory-skill/SKILL.md) and [Workflow's parallel resource audit](../workflow-skill/references/ending-resource-audit.md) for Ending. Preserve active and user review/reuse resources. End verification and code repair in the active task. Leave historical Ending test commands inert.

The optional `scripts/task_verification.py` helper selects bounded verification scope. Report helpers remain available for explicitly requested visual/PDF reports.

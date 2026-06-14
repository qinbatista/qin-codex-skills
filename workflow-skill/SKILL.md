---
name: workflow-skill
description: "Always-first global workflow controller for Codex requests. Use for every user task request before any other user/global skill for task work. It decomposes the request, defines explicit goals, selects executor skills, routes code/script/workflow work through code-skill before test-skill and verify-skill, loops until stated goals pass, and keeps process detail in the report instead of the final chat. Its routes are multi-select: combine every executor route needed by the task."
---

# Workflow Skill

Use this as the mandatory first workflow layer for user tasks. It turns a request into a target map, chooses the relevant executor skill routes, drives execution, checks whether the target is actually met, and prevents stopping before completion.

## Always-First Rule

`workflow-skill` is the entrypoint and controller. Start it before any other user/global skill when executing a task. Other skills are executors selected by `workflow-skill`; they should not be treated as independent first-entry controllers for task work.

For tiny direct answers, keep the target map implicit and lightweight, but the routing decision still belongs to `workflow-skill`.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Final deliverables go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

This skill controls a workflow with many possible executor branches. Do not run every branch just because it exists. Select every branch that matches the requested artifact and task type, and combine branches when the task spans text, code, Python, Unity C#, UI, image, document/PDF, global skill edit, optimization, management-skill for GitHub sync or auth/profile switching, or mixed work.

Read `references/routing-matrix.md` when a task spans multiple artifact types, touches global skills, or the correct route is not obvious from the request.

Use `scripts/validate_workflow_skill.py` only to validate this skill's routing contract after editing the skill.

## Trigger

Use this skill as the starting controller for user task requests before invoking any other user/global skill. For tasks that require planning, multiple steps, skill routing, testing, verification, iteration, global skill changes, or a final evidence report, write the target map explicitly. For a tiny direct answer, keep the target map implicit and lightweight.

## Workflow

Start with `workflow-skill`, run the start contract, route the necessary executor skills, execute the work, test it, verify it against the target, and loop until the stop condition is met.

## Start Contract

Before doing the work, write a short target map:

1. `Task slices`: the ordered pieces of work.
2. `Artifacts`: what will exist or change, such as text, code, image, UI, PDF, Markdown, skill files, or GitHub state.
3. `Pass targets`: what observable result proves each artifact is correct.
4. `Skill route`: the skills needed and the order they must run; the first skill must be `workflow-skill`.
5. `Stop condition`: the exact condition that allows final completion.

Make the pass target match the artifact:

- Text: required sections, wording constraints, format, and destination.
- Image: source image, output image, visible changes, dimensions or visual constraints.
- Code: behavior, real input, command or app flow, real output, and pass reason.
- UI: page or screenshot target, viewport sizes, interaction state, and visual blockers.
- Link or URL: exact URL plus response, page state, or extracted content.
- Document/PDF/report: file path, rendered or parsed content, and required evidence fields.
- Skill: frontmatter, trigger description, references, scripts, route behavior, old-name cleanup, and sync state.
- GitHub or management: local input state, command used, remote or profile result, and privacy constraints.

Begin after the target map unless the request is ambiguous, dangerous, destructive, or needs user credentials.

## Mandatory Execution Spine

For code, local scripts, automations, global-skill scripts, website/app work, or any task that creates or edits executable behavior, run this order:

```text
workflow-skill -> code-skill -> test-skill -> verify-skill -> goal check
```

- `code-skill`: executor for writing, editing, refactoring, or reasoning about code and helper scripts.
- `test-skill`: executor for small real tests with concrete input and real output. Do not accept import-only, signature-only, mock-only, or bare `OK` evidence when real usage is practical.
- `verify-skill`: executor for comparing the observed result against the original pass targets, including UI, generated artifacts, skill instructions, or process requirements.

For non-code artifacts, replace `code-skill` with the relevant production skill or direct artifact work, then still use `test-skill` and `verify-skill` when objective evidence or a report is required.

For global skill creation, deletion, rename, or editing, include `management-skill` before reading/editing and after verification when the user wants the saved skill pushed. Use the GitHub sync route inside `management-skill` for the actual mirror operation.

When a report is generated, every passing row must include `Input`, `Used`, `Output`, and `Why Pass` with real evidence.

## Completion Loop

After `test-skill` and `verify-skill`, compare the observed evidence with the target map.

- If every pass target is met, generate the final evidence report when the task produced code, a skill change, a UI/artifact change, or the user asked for proof.
- If any pass target is not met, continue from the relevant execution step, fix the issue, retest, and verify again.
- Do not stop because the method was attempted. Stop only because the target is met, the user changes the goal, or a real blocker prevents progress.

## Final Response

Keep the final chat short. State what changed, what passed, where the deliverables are, and any remaining unverified scope. Do not repeat the full process report in chat; put process details, inputs, commands, outputs, and why-pass evidence in the generated report.

## Guardrails

- Do not start a worker skill before `workflow-skill` for task work.
- Do not run every skill branch just because it exists; select every branch that is actually needed for the task.
- Do not stop before the stated pass targets are met unless there is a real blocker.
- Do not replace `test-skill` evidence with a method-only or status-only claim.
- Do not push to GitHub unless the user request or active workflow requires saved global-skill changes.

## Examples

- "Create a new skill and push it" -> decompose, use management-skill with its GitHub sync route, code-skill for scripts, test-skill, verify-skill, then sync.
- "Fix this Python script" -> decompose, use code-skill, run a real Python input through test-skill, then verify behavior.
- "Review this UI" -> decompose visual targets, use verify-skill UI route, capture real evidence, and report blockers.

## Verification

After editing this skill:

1. Run the structural validator:

   ```bash
   python3 scripts/validate_workflow_skill.py --skill-dir /Users/qin/.codex/skills/workflow-skill --output cache/workflow-skill-validation/result.json
   ```

2. Run the skill-creator quick validator when a Python with PyYAML is available.
3. Run `test-skill` with real evidence and a PDF report.
4. Run `verify-skill` against the requested outcome and the generated report.

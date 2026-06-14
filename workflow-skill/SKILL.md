---
name: workflow-skill
description: Global task workflow controller for Codex requests. Use at the start of any user task that needs decomposition, explicit goals, skill routing, code/script/workflow work, testing, verification, iteration to completion, or a final evidence report. It breaks the request into steps, defines artifact-specific pass criteria, routes code work through code-skill before test-skill and verify-skill, loops until the stated goals pass, and keeps process detail in the report instead of the final chat.
---

# Workflow Skill

Use this as the first workflow layer for user tasks. It turns a request into a target map, chooses the relevant skill routes, drives execution, checks whether the target is actually met, and prevents stopping before completion.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Final deliverables go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

This skill controls a workflow with many possible branches. Do not run every branch. Choose the branch that matches the requested artifact and task type: text, code, Python, Unity C#, UI, image, document/PDF, global skill edit, optimization, GitHub sync, auth/profile switching, or mixed work.

Read `references/routing-matrix.md` when a task spans multiple artifact types, touches global skills, or the correct route is not obvious from the request.

Use `scripts/validate_workflow_skill.py` only to validate this skill's routing contract after editing the skill.

## Start Contract

Before doing the work, write a short target map:

1. `Task slices`: the ordered pieces of work.
2. `Artifacts`: what will exist or change, such as text, code, image, UI, PDF, Markdown, skill files, or GitHub state.
3. `Pass targets`: what observable result proves each artifact is correct.
4. `Skill route`: the skills needed and the order they must run.
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

- `code-skill`: write, edit, refactor, or reason about code and helper scripts.
- `test-skill`: run a small real test with concrete input and real output. Do not accept import-only, signature-only, mock-only, or bare `OK` evidence when real usage is practical.
- `verify-skill`: compare the observed result against the original pass targets, including UI, generated artifacts, skill instructions, or process requirements.

For non-code artifacts, replace `code-skill` with the relevant production skill or direct artifact work, then still use `test-skill` and `verify-skill` when objective evidence or a report is required.

For global skill creation, deletion, rename, or editing, include `github-sync` before reading/editing and after verification when the user wants the saved skill pushed.

When a report is generated, every passing row must include `Input`, `Used`, `Output`, and `Why Pass` with real evidence.

## Completion Loop

After `test-skill` and `verify-skill`, compare the observed evidence with the target map.

- If every pass target is met, generate the final evidence report when the task produced code, a skill change, a UI/artifact change, or the user asked for proof.
- If any pass target is not met, continue from the relevant execution step, fix the issue, retest, and verify again.
- Do not stop because the method was attempted. Stop only because the target is met, the user changes the goal, or a real blocker prevents progress.

## Final Response

Keep the final chat short. State what changed, what passed, where the deliverables are, and any remaining unverified scope. Do not repeat the full process report in chat; put process details, inputs, commands, outputs, and why-pass evidence in the generated report.

## Verification

After editing this skill:

1. Run the structural validator:

   ```bash
   python3 scripts/validate_workflow_skill.py --skill-dir /Users/qin/.codex/skills/workflow-skill --output cache/workflow-skill-validation/result.json
   ```

2. Run the skill-creator quick validator when a Python with PyYAML is available.
3. Run `test-skill` with real evidence and a PDF report.
4. Run `verify-skill` against the requested outcome and the generated report.

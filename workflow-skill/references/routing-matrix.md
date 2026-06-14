# Workflow Routing Matrix

Use this matrix to choose only the branch needed for the current request. These rows are alternatives, not a checklist.

| Scenario | Use when | Goal target | Skill route | Evidence |
|---|---|---|---|---|
| text | User asks for text, markdown, explanation, classification, or rewrite without executable changes. | Required content, format, destination, omissions, and language are explicit. | workflow-skill -> verify-skill | Final text or file content plus why it matches the requested format. |
| code | User asks to write, edit, debug, refactor, review, or explain code. | Real behavior, concrete input, command or app path, real output, and pass reason are explicit. | workflow-skill -> code-skill -> test-skill -> verify-skill | Code path, command/tool used, stdout/result/file, and why the behavior passes. |
| python | User asks for Python scripts, modules, tests, snippets, or Python prompt assignments. | Python-specific style and behavior are explicit, including a real runnable example. | workflow-skill -> code-skill -> test-skill -> verify-skill | Python command, concrete input files or values, output, and pass reason. |
| unity-csharp | User works in a Unity project or asks for Unity C# gameplay, editor, MonoBehaviour, ScriptableObject, or manager code. | Unity behavior, lifecycle method, scene/editor expectation, and compile or runtime evidence are explicit. | workflow-skill -> code-skill -> test-skill -> verify-skill | Unity compile/editor/runtime evidence where practical, plus the changed C# path and observed behavior. |
| prompt | User asks to generate, rewrite, or embed an AI prompt. | Prompt purpose, variables, output shape, and embedding destination are explicit. | workflow-skill -> code-skill -> test-skill -> verify-skill | Generated prompt text or code assignment, sample input when practical, resulting output shape, and pass reason. |
| ui | User asks to build, change, review, or verify UI, frontend, layout, screenshots, visual quality, or responsive behavior. | Target page/state, viewport sizes, visual acceptance criteria, and blockers are explicit. | workflow-skill -> code-skill -> test-skill -> verify-skill | Screenshot paths, browser state, viewport sizes, console/runtime evidence, and why UI passes. |
| image | User asks for image generation, editing, comparison, or visual artifact review. | Source/output images, dimensions, visible changes, and visual acceptance criteria are explicit. | workflow-skill -> test-skill -> verify-skill | Input image or prompt, generated image path, visual inspection result, and pass reason. |
| document-pdf | User asks for documents, PDFs, reports, exported files, or evidence PDFs. | Output file path, required sections, rendered or parsed content, and evidence fields are explicit. | workflow-skill -> test-skill -> verify-skill | File path, parser/render command, extracted text or preview, and pass reason. |
| skill-edit | User asks to create, merge, rename, delete, reorganize, or update global Codex skills. | Skill names, frontmatter, trigger behavior, references/scripts, old-name cleanup, validation, and GitHub sync target are explicit. | workflow-skill -> management-skill -> code-skill -> test-skill -> verify-skill -> management-skill | Skill files, validation commands, generated overview/report, sync status, remote hash, and pass reason. |
| optimization | User asks to optimize a repeated skill or fixed workflow into local files, scripts, references, or assets. | Repeated process, reusable script or resource type, input/output contract, and speed/token-saving target are explicit. | workflow-skill -> optimization-skill -> code-skill -> test-skill -> verify-skill | Reference/source inputs, generated script or resource, real run output, and pass reason. |
| github-sync | User asks to sync, commit, push, inspect, or publish global skills to GitHub. | Repository, mirror scope, public-safety requirements, local/remote state, and expected final hash are explicit. | workflow-skill -> management-skill -> verify-skill | Status output, safety scan, pushed commit hash or no-diff result, and pass reason. |
| codex-switch | User asks to inspect or switch local Codex auth profiles. | Requested profile action, local-only scope, confirmation requirement, and privacy constraints are explicit. | workflow-skill -> management-skill -> verify-skill | Local profile command output or file state, no token disclosure, and pass reason. |
| mixed | User request spans multiple artifact types or several skills. | Each per-artifact target has its own pass target and the overall stop condition plus unresolved scope are explicit. | workflow-skill -> relevant production skill(s) -> test-skill -> verify-skill | Per-artifact input, used method, output, why-pass evidence, and unresolved scope if any. |

## Goal Check Rules

- Every route starts with `workflow-skill`.
- For executable behavior, the order must be `code-skill -> test-skill -> verify-skill`.
- For global skill work, run `management-skill` before edits and after successful verification when the user asks to push; the management route selects `github-sync`.
- Passing evidence must include real `Input`, `Used`, `Output`, and `Why Pass` when a report is generated.
- If the observed output does not satisfy the goal target, continue the loop instead of finishing.

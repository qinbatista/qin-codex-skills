---
name: prompt-skill
description: "Use to create, review, edit, or test reusable prompts and durable AI instructions, including prompts in code and image workflows. Ordinary prose does not trigger it."
---

# Prompt Skill

Before the first write of support, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md); prompts keep their owner.

## Scope

Read relevant [project memory](../project-memory-skill/SKILL.md) on every task; skip it when unavailable. Recall exact prompt/module/file/symbol context, not whole history. Keep project facts scoped to that project and global preferences separate. Label cross-project examples as references. Current instructions and fresh source override stale memory.

## Design

State the objective, necessary inputs and their roles, requirements, and output contract. Include success/failure criteria and a verification step when they improve acceptance. Define placeholders, units, enums, missing-value behavior, and reference authority only where relevant.

Limit responses to the requested fields, values and format; prohibit unrequested metadata, explanations, wrappers and duplicated content. For color-only JSON require `{"color":"blue"}`; for a choice-only answer require just `1`. Allow additions explicitly requested or required by the actual schema, validator, safety or failure contract. Preserve distinct source facts and required evidence; check the consumer before removing existing fields.

Keep one authoritative rule per behavior. Merge repeated warnings into a clear rule, resolve contradictions, and remove obvious instructions that add no constraint. Use role, tool order, autonomy limits, verbosity targets, delimiters, or examples only when they change the result. Examples illustrate rules; they do not override them. Do not request private chain-of-thought or force visible planning.

Separate stable policy from per-run data. Ask only for a material missing decision; otherwise state a reasonable assumption. Correct unambiguous spelling in durable instructions; follow [correct task names](../task-analyze-skill/SKILL.md#correct-task-names). Preserve quoted user prose, user data, external names, and persisted/public contracts.

Apply [Management's authoring rules](../management-skill/SKILL.md#authoring-rules): write durable instructions in English, move deterministic steps to local code and simplify before adding instructions.

## Workflow

1. Inspect the existing prompt, its direct consumer/validator, relevant inputs, and observed failures.
2. Identify the desired result and replace the weakest ambiguous or conflicting rule with the smallest complete instruction.
3. Verify within this active task. For consequential output behavior, use representative inputs and inspect semantic correctness as well as format. Read back simple value-only edits. Do not start the whole project or compile it merely to check a prompt unless requested.
4. Return the artifact and concise evidence under [Task Analyze's action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests). State when a provider trial or stochastic reliability remains untested; one good sample does not prove stability.
5. Ending's memory branch consolidates useful knowledge; it performs no product verification or code repair. [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md) releases disposable resources and preserves user review/reuse.

## Output-specific checks

| Output | Relevant contract |
| --- | --- |
| Structured data | Schema, exact permitted fields, types, allowed missing values, and cross-field consistency; no unsolicited keys |
| Human-readable content | Requested answer only, audience, factual support, terminology, and useful length/organization |
| Image or multimodal output | Each reference's role; what stays fixed; count, pose, crop, aspect ratio, and actual file/transparency requirements |
| Prompt in executable code | [Code Skill](../code-skill/SKILL.md) and [string integration](../code-skill/references/prompt-generation.md) for syntax, interpolation, and consumers |
| Functional code shipped in Skills | [Skill platform compatibility](../code-skill/references/skill-platform-compatibility.md) |

Image acceptance distinguishes visible fidelity from file validity: a checkerboard is not alpha, and a downloaded file is not proof of correct structure. Match checks to the actual intended use rather than inserting sprite-specific restrictions into every image prompt.

Actual image jobs follow [image generation and closure](../workflow-skill/references/image-generation.md); keep prompt acceptance separate from native delivery, verified owner synchronization, account deletion/readback, and owned-tab closure.

## Guardrails

Preserve user authority and the authorized scope. Do not weaken acceptance criteria to make an output pass. Use the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md) when creating support artifacts. Keep reusable instructions concise enough that a capable model can apply the goal without a ritual checklist.

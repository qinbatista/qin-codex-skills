---
name: prompt-skill
description: "Use to create, review, edit, or test reusable prompts and durable AI instructions, including prompts in code and image workflows. Ordinary prose does not trigger it."
---

# Prompt Skill

## Scope

Use the user's selected model and effort for prompt design and delegated prompt work. Read the relevant project memory on every task through [project memory](../project-memory-skill/SKILL.md); skip it when unavailable. Keep project facts scoped to that project, and explicit global preferences separate. Current instructions and fresh source override stale memory.

## Design

State the objective, necessary inputs and their roles, requirements, and output contract. Include success/failure criteria and a verification step when they improve acceptance. Define placeholders, units, enums, missing-value behavior, and reference authority only where relevant.

Keep one authoritative rule per behavior. Merge repeated warnings into a clear rule, resolve contradictions, and remove obvious instructions that add no constraint. Use role, tool order, autonomy limits, verbosity targets, delimiters, or examples only when they change the result. Examples illustrate rules; they do not override them. Do not request private chain-of-thought or force visible planning.

Separate stable policy from per-run data. Ask only for a missing decision that materially changes the result; otherwise proceed with a reasonable stated assumption. Correct unambiguous spelling in new durable instructions and report the original-to-canonical mapping when material. Preserve quoted user prose, user data, external names, and persisted/public contracts.

## Workflow

1. Inspect the existing prompt, its direct consumer/validator, relevant inputs, and observed failures.
2. Identify the desired result and replace the weakest ambiguous or conflicting rule with the smallest complete instruction.
3. Verify within this active task. For consequential output behavior, use representative inputs and inspect semantic correctness as well as format. For a simple value-only edit, skip verification. Do not start the whole project or compile it merely to check a prompt unless requested.
4. Return the artifact and concise evidence. State when a provider trial or stochastic reliability remains untested; one good sample does not prove stability.
5. Ending only summarizes useful project memory from completed work, using the user's selected model and effort. It performs no verification or repair.

## Output-specific checks

| Output | Relevant contract |
| --- | --- |
| Structured data | Schema, required fields, types, allowed missing values, and cross-field consistency |
| Human-readable content | Audience, factual support, terminology, and useful length/organization |
| Image or multimodal output | Each reference's role; what stays fixed; count, pose, crop, aspect ratio, and actual file/transparency requirements |
| Prompt in executable code | [Code Skill](../code-skill/SKILL.md) and [string integration](../code-skill/references/prompt-generation.md) for syntax, interpolation, and consumers |
| Functional code shipped in Skills | [Skill platform compatibility](../code-skill/references/skill-platform-compatibility.md) |

Image acceptance distinguishes visible fidelity from file validity: a checkerboard is not alpha, and a downloaded file is not proof of correct structure. Match checks to the actual intended use rather than inserting sprite-specific restrictions into every image prompt.

## Guardrails

Preserve user authority and the authorized scope. Do not weaken acceptance criteria to make an output pass. Use [project Cache policy](../workflow-skill/references/project-cache-artifact-policy.md) only when creating support artifacts. Keep reusable instructions concise enough that a capable model can apply the goal without a ritual checklist.

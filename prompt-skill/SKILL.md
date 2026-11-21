---
name: prompt-skill
description: "Use to create, review, edit, or test reusable prompts and durable AI instructions, including prompts in code and image workflows. Ordinary prose does not trigger it."
---

# Prompt Skill

Keep prompts with their owners and support in project Cache from its first write under the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md).

## Scope

On every task, recall exact prompt/module/file/symbol context from [project memory](../project-memory-skill/SKILL.md) and skip it when unavailable. Keep project facts scoped to that project and shared preferences with their owner. Label cross-project examples as references. Current instructions and fresh source take precedence.

## Design

Specify the objective, inputs and their roles, requirements and output contract. Add success/failure criteria and verification when useful. Define relevant placeholders, units, enums, missing-value behavior and reference authority.

Require the exact requested fields, values and format, such as `{"color":"blue"}` for color-only JSON or just `1` for a choice-only answer. Allow extra metadata, prose or wrappers only when the request, schema, validator, safety or failure contract requires them. Omit duplicate content and preserve distinct source facts and required evidence. Check the consumer before removing fields.

Keep one authoritative rule per behavior, resolve contradictions and remove repetition. Use roles, tool order, autonomy limits, verbosity, delimiters and examples only when they change the result. Examples illustrate rules and follow their precedence. Avoid requests for private chain-of-thought or mandatory visible planning.

Separate stable policy from run data. State reasonable assumptions and ask only for material decisions. Correct unambiguous spelling under [correct task names](../task-analyze-skill/SKILL.md#correct-task-names). Preserve quoted user prose, user data, external names and persisted/public contracts.

Follow [Management's authoring rules](../management-skill/SKILL.md#authoring-rules) for English instructions, deterministic tooling and simplification.

## Workflow

1. Inspect the existing prompt, direct consumer or validator, relevant inputs and observed failures.
2. Replace ambiguous or conflicting guidance with the smallest complete instruction.
3. Verify within this active task. Check semantic correctness and format with representative inputs. Read back simple value-only edits. Do not start the whole project or compile it to check a prompt unless requested.
4. Deliver the artifact and evidence under [Task Analyze's action completion rule](../task-analyze-skill/SKILL.md#complete-action-requests). Report untested provider behavior or repeatability. For repeatability, one good sample does not prove stability.
5. Ending's memory branch consolidates facts through [inline closeout](../project-memory-skill/SKILL.md#inline-guidance-memory-and-resource-closure) and performs no product verification or code repair. Use [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md) for resource closure.

## Output-specific checks

| Output | Relevant contract |
| --- | --- |
| Structured data | Schema, exact permitted fields, types, allowed missing values, and cross-field consistency; no unsolicited keys |
| Human-readable content | Requested answer only, audience, factual support, terminology, and useful length/organization |
| Image or multimodal output | Each reference's role; what stays fixed; count, pose, crop, aspect ratio, and actual file/transparency requirements |
| Prompt in executable code | [Code Skill](../code-skill/SKILL.md) and [string integration](../code-skill/references/prompt-generation.md) for syntax, interpolation, and consumers |
| Functional code shipped in Skills | [Skill platform compatibility](../code-skill/references/skill-platform-compatibility.md) |

Match image checks to the intended use. A checkerboard is not alpha. Verify actual alpha and file structure when required, alongside any visual fidelity checks. Apply format-specific restrictions only when the receiving asset requires them.

For actual image jobs, verify prompt acceptance on its own. Apply [image generation and closure](../workflow-skill/references/image-generation.md) for native delivery, owner synchronization, account deletion/readback and owned-tab closure.

## Guardrails

Preserve user authority, authorized scope and acceptance criteria when revising a prompt or diagnosing a failing output.

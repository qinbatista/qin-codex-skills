---
name: prompt-skill
description: "Always use for every task whose requested work creates, reviews, edits, repairs, standardizes, tests, summarizes, optimizes, or changes a reusable prompt or durable AI instruction, including system/developer/agent/Custom GPT instructions, image-generation prompts, prompt templates, and prompts embedded in code, config, or workflows. This is the 100% global prompt-task gate across projects. Do not trigger merely because an ordinary request is text. Prompt-in-code also uses its owning code executor; code-skill owns Python and C#."
---

# Prompt Skill

## Scope

This is the 100% global prompt-task gate across projects. Load it before any task creates, reviews, edits, repairs, standardizes, tests, summarizes, optimizes, or changes a reusable prompt or durable AI instruction. It covers system/developer/agent/Custom GPT instructions, image-generation prompts, prompt templates, and prompts embedded in code, config, or workflows. Ordinary prose does not trigger it merely because it is text. Prompt-in-code also loads its owning code executor; `code-skill` owns Python and C#.

For an existing prompt, read the complete target prompt and its direct validator as execution input. This is the prompt-work exception to the ordinary exact-read-only no-skill shortcut; it does not authorize broad repository reading, Task Analyze, Workflow, child models, or pre-result verification. If this gate was missed, stop before more prompt changes and redo the prompt work under this skill.

## Core Contract

Every production prompt must make the following behavior explicit when it materially affects the result:

1. **Objective** — the concrete final outcome; never make the model infer the job.
2. **Context and inputs** — relevant environment, audience, source material, variable placeholders, reference roles, and known limitations.
3. **Requirements and constraints** — required behavior, prohibited behavior, authority/autonomy boundary, and instruction priority.
4. **Output contract** — exact artifact, schema, count, layout, format, destination, and response length where applicable.
5. **Success criteria** — measurable conditions that make the result usable.
6. **Failure conditions** — observable conditions that reject the result even when an artifact was produced.
7. **Verification** — checks performed before acceptance and the evidence or receipt that records them.

Role, workflow steps, reasoning effort, verbosity, examples, and delimiters are optional controls. Add them only when they improve behavior; do not add ceremonial sections or persona filler.

## Conditional Controls

Use these controls deliberately instead of inserting them into every prompt:

| Control | Use it when | Rule |
|---|---|---|
| Role | A domain perspective, audience, or decision standard changes the result | Name the useful expertise and responsibility; omit fictional biography and generic `You are helpful` text. |
| Workflow and tool order | Sequence, dependencies, or side effects affect correctness | State the minimum ordered actions, allowed tools, stop condition, and fallback. Do not force a visible plan for a one-step task. |
| Autonomy and ambiguity | The model may need to choose, assume, ask, or act | Define what it may decide, when a bounded assumption is acceptable, and which missing facts require a question. |
| Reasoning effort | Risk or complexity justifies more analysis | Request only the necessary effort and concise rationale/checks; never request private chain-of-thought or maximum reasoning by default. |
| Verbosity | Length, audience, or review cost matters | Give a measurable word, section, item, or detail target instead of `brief but detailed`. |
| Delimiters | Multiple instruction, source, example, or data blocks could be confused | Use named tags or fenced blocks and state each block's role and authority. |
| Few-shot examples | A schema, style, boundary, or edge case remains ambiguous after direct rules | Use the fewest representative examples, label input/output clearly, and make explicit rules authoritative over examples. |

Negative instructions are appropriate for critical, plausible failures such as fabrication, unsafe actions, forbidden fields, or copying the wrong reference. Express ordinary behavior positively and measurably; do not build a prompt from a long history of `do not` warnings.

## Consistency And Priority

- Follow the active instruction hierarchy and keep one authoritative rule for each behavior.
- Resolve contradictions before delivery. When two preferences compete, use the objective, audience, output contract, and higher-authority instruction to choose one observable behavior.
- Define every placeholder, source role, unit, enum, count, and destination that affects acceptance.
- Prefer explicit and measurable instructions over vague quality language. Replace `make it good` with the property and check that prove good.
- Treat examples as illustrations, never as permission to override constraints or invent unavailable facts.

## Workflow

1. Inspect the existing prompt, real inputs, bad outputs, and current validator before editing.
2. State internally: `Prompt idea -> Prompt goal -> observed problems -> smallest complete solution`.
3. Separate durable rules from per-run variables. Keep static policy in the reusable prompt and pass changing subject/input values through named placeholders or attachments.
4. Resolve contradictions and precedence first. Merge overlapping negatives into one positive, testable rule rather than accumulating warnings.
5. Select only the conditional controls that materially reduce ambiguity or failure risk.
6. Preserve user authority. Ask only when missing information would materially change the result or create high-risk/external effects; otherwise make and disclose a bounded assumption.
7. Build the prompt in this order when applicable: objective, context/inputs, requirements/constraints, conditional controls, output contract, success/failure conditions, and verification.
8. For complex work, plan dependencies internally before execution and use `plan -> execute -> review -> finalize` only when those phases improve the result. Do not expose a planning preamble or private reasoning unless the user explicitly requests an appropriate planning artifact.
9. Put tool order in the prompt only when order affects correctness or side effects. Name the tool purpose, required evidence, fallback, and stop condition when tools are part of the contract.
10. Present the completed prompt or instruction artifact immediately. Do not put an external trial run, validator, report, or closeout step before that first presentation.
11. Start the mandatory independent Ending lifecycle as a <=60-second read-only handoff audit. It does not test prompt cases; representative trials or repeated fresh runs happen only when the user explicitly requests testing.
12. Grade artifact production separately from acceptance. A downloaded image, valid JSON container, or completed model response is not a pass when semantic, file, structure, or visual gates fail.
13. If the Ending audit lacks evidence or sees concurrent state change, record terminal BLOCKED and exit without a user question or automatic repair. A repair or prompt trial is a new explicit user task.

## Recommended Prompt Shape

Use the smallest subset that fully controls the task:

```text
Role: <only when domain perspective matters>

Objective:
<one concrete outcome>

Context and inputs:
- <source or variable role>
- <environment or limitation>

Requirements:
- <required capability>

Constraints:
- <hard boundary or prohibition>

Workflow:
1. <ordered step only when order matters>

Autonomy and ambiguity:
- <what may be decided or assumed; what requires a question>

Effort and verbosity:
- <only when a measurable level or response limit matters>

Output contract:
<exact format, count, schema, layout, or file contract>

Success criteria:
- <measurable acceptance condition>

Failure conditions:
- <observable rejection condition>

Verification:
- <check and evidence>

Examples:
<only the minimum labeled examples needed to remove ambiguity>
```

The headings are a design aid, not a mandatory ceremony. Preserve a project's established prompt style when the same contract is explicit and testable.

## Image And Multimodal Prompts

- Assign every attachment one role: subject/structure, style, context, data-channel, or edit target. State what must not be copied from each reference.
- Make camera, pose, count, ordering, aspect ratio, crop, transparency/background, and file-mode requirements measurable.
- Separate semantic fidelity from file validity. Check both the visible image and the downloaded bytes.
- For isolated sprites, distinguish real RGBA from a baked checkerboard and reject detached shadows, glow, particles, or meaningful alpha outside the body.
- For sketch-to-image, count and preserve required structural strokes/parts before adding style detail.
- For image-to-image and variants, specify what is locked and what is allowed to change.
- For production stability, compare identical inputs across fresh runs and report automatic/file gates separately from manual visual gates.

## Structured Output Prompts

- Prefer a schema or one valid example over repeated prose about formatting.
- Define allowed missing-value behavior; never let the model invent unavailable values.
- Validate parsing, required fields, types, enums, naming, and cross-field consistency.
- In code strings, escape literal braces correctly while leaving real interpolation placeholders unescaped.

## Acceptance Checklist

Before accepting a production prompt, confirm:

- the objective and final artifact are unambiguous;
- every material input, placeholder, reference, and authority boundary is defined;
- requirements are explicit, constraints are non-conflicting, and measurable limits replace vague preferences;
- role, workflow, tools, autonomy, effort, verbosity, delimiters, and examples appear only when useful;
- the output contract defines format, count/schema/layout, missing-value behavior, and destination where relevant;
- success and failure conditions can reject a merely completed but incorrect artifact;
- verification checks the actual semantic, structural, file, visual, or side-effect requirements without requesting private chain-of-thought.
- when final target-output validation matters, the prompt tells the target model to check missing fields, invalid format or JSON, unsupported claims, inconsistent terminology, and requirement violations before returning; it corrects a failed check when possible or follows the defined failure contract.

## Guardrails

- Do not require a plan in the user-visible response unless the user asked for one or planning is itself the deliverable.
- Do not expose private chain-of-thought. Request concise rationale, evidence, or checks instead.
- Do not use "ask instead of guess" as a blanket blocker; it must respect the active autonomy and authorization rules.
- Do not use maximum reasoning, long output, or many examples by default. Match effort and verbosity to task risk and complexity.
- Do not make every task follow a visible step-by-step or `plan -> execute -> review` ceremony. Use ordered phases only when they change correctness or control risk.
- Do not let examples silently become requirements or override explicit instructions.
- Do not claim stability from one attractive sample.
- Do not weaken acceptance criteria to make a failing prompt appear successful.

## Handoff

Return the updated prompt or instruction artifact first, followed by a compact change summary, test cohort, pass/fail results, and known remaining risks. If the prompt is embedded in executable code, also follow the owning code executor; use `code-skill` and its language-specific rules for Python and C#.

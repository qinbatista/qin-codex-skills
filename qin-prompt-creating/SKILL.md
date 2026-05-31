---
name: qin-prompt-creating
description: Create and optimize purpose-specific Python f-string prompts for AI tasks using a consistent Purpose + Rules structure. Use automatically when the user needs a prompt created, rewritten, improved, standardized, shortened, or reviewed, even if they do not name this skill. Especially use for direct function prompts for extraction, coordinates, transformation, checking, fixing structured data, and human-reading content prompts for factories, doctors, customers, reviewers, or other audiences where purpose and return JSON format must be clear.
---

# Qin Prompt Creating

## Overview

Create compact Python prompt assignments that are ready to paste into code:
`prompt = f"""..."""`.

Choose one of two patterns:

- Function prompt: direct AI operation for getting coordinates, extracting information, changing information, checking or fixing structured data, or a similar task output.
- Content prompt: human-facing result text such as descriptions, summaries, explanations, factory notes, doctor-facing notes, customer-facing copy, or other readable sentences.

## Trigger

Use this skill automatically whenever the user needs an AI prompt created, optimized, rewritten, reviewed, or standardized. Do not wait for the user to name `$qin-prompt-creating` when the task is clearly prompt work, especially when the prompt will live in Python code as an f-string and needs JSON examples or return schemas.

## Workflow

1. Identify the prompt purpose, input variables, target audience, and desired output shape.
2. Choose function prompt when the prompt is an instruction for an AI or tool to perform a direct operation. Choose content prompt when the prompt produces text a human will read.
3. Return the final prompt as a Python f-string assignment:

```python
prompt = f"""
...
"""
```

4. Escape every literal JSON brace inside the f-string: use `{{` and `}}` for JSON objects. Keep real f-string interpolation placeholders as single braces, such as `{image_width}`.
5. Keep the prompt concise. Merge overlapping rules instead of appending repeated warnings.
6. Treat user examples, bad outputs, and edge cases as test evidence first. Do not copy them into the prompt as literal case rules unless the example itself is the reusable requirement.
7. For function prompts, always use an explicit `Purpose:` block followed by a `Rules:` block. Do not start with a persona or role sentence such as `You are...`.
8. Make the output schema the contract. When the schema already shows the object, list, keys, and field names, avoid extra format warnings such as `do not return a list`, `top-level key`, or `do not add fields`. If the caller uses OpenAI JSON mode, write `Output JSON format must be:` so the prompt satisfies the API without verbose JSON warnings.
9. Include only rules that materially shape the output direction or prevent a plausible wrong interpretation.

## Existing Prompt Optimization

When optimizing a current prompt, read the full prompt first and preserve its real task, inputs, required output fields, and hard constraints.

Then rewrite it into the matching pattern and keep the top-level structure as `Purpose:` followed by `Rules:`:

- Function direction prompt when the prompt asks an AI to get, extract, change, check, fix, convert, compare, or return structured task output.
- Content direction prompt when the prompt asks for sentences, descriptions, summaries, notes, copy, or other human-readable text.

Optimization rules:

- Remove duplicate, vague, obvious, or tiny rules.
- Keep only constraints that change the model's direction, evidence source, audience, format, or allowed content.
- Keep the final prompt shorter than the original unless the original is missing a necessary purpose, schema, or hard constraint.
- Preserve valid JSON schemas and fix f-string JSON escaping.
- Return only the optimized `prompt = f"""..."""` unless the user asks for explanation.

## Function Prompts

Use an explicit `Purpose:` block from the function perspective: what the function should do, what source it uses, and what result it returns. Then add short rules and a structured result format.

Required shape:

```python
prompt = f"""
Purpose:
Get <target> from <source>.

Rules:
- <rule 1>
- <rule 2>

Output JSON format must be:
{{
  "<key>": "<value>"
}}
"""
```

Guidelines:

- Start `Purpose:` with the action and objects, not background explanation.
- Keep `Purpose:` function-centered, such as `Check X`, `Extract Y`, `Convert A to B`, or `Return Z`.
- Do not start with role/persona setup such as `You are a...`; write the purpose and expected result directly.
- Use command wording: Get, Extract, Change, Check, Fix, Convert, Compare, Return.
- Put constraints under `Rules`.
- Put only the required schema under `Output format must be:` when that is enough; use `Output JSON format must be:` for OpenAI JSON-mode calls. Let the schema define the container shape and fields instead of repeating them in prose.
- For coordinates, use a `Coordinates rule:` block when source selection and circle coverage are important. Include source image meaning, coordinate units/order, and what the circle must cover.
- Merge short source/context guidance into the task line when it fits; avoid a separate source section for one sentence of context.
- Do not add audience-purpose prose unless the result is meant for human reading.

## Human-Reading Content Prompts

Use this when the output will be read by factories, doctors, customers, reviewers, clients, or another real audience. In content prompts, the `Purpose:` block should describe the working role or perspective producing the content, not only the mechanical output action.

Required shape:

```python
prompt = f"""
Purpose:
Work from the perspective of <role> writing <content type> from <source/input> for <audience/use case>, emphasizing <most important purpose-specific qualities> first.

Rules:
- <rule 1>
- <rule 2>

Return JSON Format:
{{
  "<key>": "<value>"
}}
"""
```

Guidelines:

- Start with `Purpose:` before style, formatting, or output rules.
- Keep `Purpose:` role-centered, such as a factory technical writer, ecommerce copywriter, doctor-facing summarizer, reviewer, or customer-support agent working on the content.
- Name the audience and usage context directly.
- Make rules about clarity, tone, sensitivity, omissions, and practical use.
- Ask for natural sentences when the result should read like prose.
- Keep JSON keys useful for downstream code, but keep text values human-readable.

## Rule Quality

Rules must be hard directional constraints, not generic reminders or tiny limitations.

Good rules change what the model should choose, include, exclude, or prioritize:

- Use only directly visible garment evidence.
- Write for factory production teams, not customers.
- Keep the output in factory BOM row names, not visual descriptions.
- Use a flat technical sketch style with no lifestyle background.

Do not add obvious rules that merely restate the base task or normal quality expectations:

- Do not say an image must match the user's description.
- Do not say to create the requested image.
- Do not add generic failure-prevention rules such as no pure black image, no pure white image, or no blank image unless the user explicitly asked for that constraint.
- Do not add small style limitations that do not materially affect the requested result.

## F-String JSON Rules

- Literal JSON braces must be doubled: `{{` and `}}`.
- Real Python variables stay single-braced: `{product_name}`, `{image_width}`, `{source_json}`.
- Arrays do not need escaping, but object braces inside arrays still do.
- Do not output invalid examples like `{ "items": [] }` inside an f-string. Use `{{ "items": [] }}`.
- If a JSON string value is an f-string placeholder, write it as `"source": "{source_name}"` inside doubled object braces.

## Guardrails

- Do not wrap the prompt in explanation unless the user asks for commentary.
- Do not append duplicate warnings. Replace repeated requirements with one direct rule.
- Do not paste test cases into prompts. Reproduce or inspect the result, identify the general prompt gap, and leave the prompt unchanged when the existing prompt already covers the case.
- Do not add persona openings like `You are...` to function prompts when a direct task sentence is enough.
- Do not write prompts as loose paragraphs. Use `Purpose:` then `Rules:`.
- Avoid separate `Return strict JSON`, `top-level key`, `do not return a list`, or `do not add fields` rules when the schema already communicates the contract.
- Do not use vague filler such as "be accurate" when a concrete rule can say what accuracy requires.
- Do not add obvious filler rules such as "match the user request" or "avoid blank output"; use rules only when they constrain the direction, audience, evidence source, format, or allowed content.
- Do not leave literal JSON braces unescaped inside `prompt = f"""..."""`.

## Examples

Function prompt:

```python
prompt = f"""
Purpose:
Get label circle coordinates from the {source_name} garment image.

Image size: {image_width} x {image_height} pixels.

Rules:
- Use only visible label or tag pixels.
- Do not infer hidden or expected labels.

Output format must be:
{{
  "label_coordinates": [
    {{"name": "string", "coordinates": [0, 0, 0]}}
  ]
}}
"""
```

Content prompt:

```python
prompt = f"""
Purpose:
Work from the perspective of an ecommerce product copywriter writing customer-facing product description sentences from the product details for customers reading a product page, emphasizing visible design, material feel, fit, and purchase-relevant clarity first.

Rules:
- Write natural sentences, not internal labels or production notes.
- Do not invent care instructions, certifications, or performance claims.

Return JSON Format:
{{
  "description": "string",
  "highlights": ["string"]
}}
"""
```

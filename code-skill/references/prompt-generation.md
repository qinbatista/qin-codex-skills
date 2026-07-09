# Prompt Generation

Use this route only for Python/C# AI prompt-related work: creation, review, testing, editing, add/update/remove/rewrite, improvement, standardization, or prompt embedding in Python or C# code. Do not use it for ordinary code style, architecture, debugging, non-prompt prose, or prompt snippets in other programming languages.

Create compact Python prompt assignments or C# prompt constants ready to paste into code:

```python
prompt = f"""
...
"""
```

```csharp
const string prompt = """
...
""";
```

## Workflow

1. Start by showing the prompt-purpose workflow: `Prompt idea -> Prompt goal -> Problems -> Solution`.
2. Identify purpose, input variables, target audience, and desired output shape.
3. For an existing prompt, read it seriously and identify the failing or missing behavior before changing wording.
4. Choose a function prompt for direct AI operations such as get, extract, change, check, fix, convert, compare, or return structured output.
5. Choose a content prompt for text humans will read, such as descriptions, summaries, explanations, factory notes, doctor-facing notes, customer copy, or reviewer notes.
6. Use `Purpose:` followed by `Rules:`.
7. Keep the prompt complete and concise. Add missing logic when the prompt does not cover the task goal; merge overlapping rules instead of appending repeated warnings.
8. State durable rules at the highest useful level. Do not add obvious prohibitions, near-duplicate warnings, or case-by-case exclusions.
9. Treat examples, bad outputs, and edge cases as test evidence. Do not paste them into the prompt unless the example is the reusable requirement.
10. Test the prompt with a representative input/output scenario when practical; otherwise inspect the prompt against the output contract and note why that is enough.
11. For Python f-strings, escape literal JSON braces as `{{` and `}}`; real interpolation placeholders stay single-braced, such as `{image_width}`.

## Function Prompt Shape

```python
prompt = f"""
Purpose:
Extract <target> from <source>.

Rules:
- <rule 1>
- <rule 2>

Output JSON format must be:
{{
  "<key>": "<value>"
}}
"""
```

## Human-Reading Content Prompt Shape

```python
prompt = f"""
Purpose:
Work from the perspective of <role> writing <content type> from <source/input> for <audience/use case>, emphasizing <most important qualities> first.

Rules:
- <rule 1>
- <rule 2>

Return JSON Format:
{{
  "<key>": "<value>"
}}
"""
```

## Guardrails

- Do not start function prompts with persona text such as `You are...`.
- Let the output schema define the container shape and fields instead of repeating verbose JSON warnings.
- Do not add sibling-case warnings for cases the user did not mention.
- Do not add obvious prohibitions that already follow from the purpose, rules, or output contract.
- Do not add vague filler such as "be accurate" when a concrete rule can say what accuracy requires.
- Do add necessary logic when the prompt lacks it. Do not keep adding repeated prompt rules to cover every observed failure; replace the weak block with a complete working rule that matches the prompt goal.
- Return the optimized Python assignment or C# constant after the required purpose workflow when the user asks for prompt code only.

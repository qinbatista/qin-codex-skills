# Prompt Generation

Use this route only for AI prompt-related work embedded in an active registry-owned code domain: creation, review, testing, editing, add/update/remove/rewrite, improvement, or standardization. Current examples are Python and C#. Do not use it for ordinary code style, architecture, debugging, non-prompt prose, or prompt snippets outside the planned code domain.

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

Always apply the global `prompt-skill` first. A missing or skipped `prompt-skill` is a prompt-task routing failure. This reference only specializes that normative contract for prompts stored in executable Python or C#; it never weakens the objective, context/input roles, requirements/constraints, output contract, measurable success/failure conditions, or verification gates.

1. Use `Prompt idea -> Prompt goal -> observed problems -> smallest complete solution` internally. Do not print this planning scaffold in the generated prompt or user-facing result.
2. Identify objective, context/input roles, variables, target audience, requirements, constraints, output contract, measurable success criteria, observable failure conditions, and verification.
3. For an existing prompt, read it seriously and identify the failing or missing behavior before changing wording.
4. Choose a function prompt for direct AI operations such as get, extract, change, check, fix, convert, compare, or return structured output.
5. Choose a content prompt for text humans will read, such as descriptions, summaries, explanations, factory notes, doctor-facing notes, customer copy, or reviewer notes.
6. Use the smallest applicable canonical structure: `Objective`, `Context and inputs`, `Requirements`, `Constraints`, optional controls, `Output contract`, `Success criteria`, `Failure conditions`, and `Verification`. Existing project headings may stay when they express the same contract clearly.
7. Add role, ordered workflow/tools, autonomy, reasoning level, verbosity, delimiters, or examples only when each one changes behavior or removes a real ambiguity.
8. Keep the prompt complete and concise. Add missing logic when the prompt does not cover the task goal; merge overlapping rules instead of appending repeated warnings.
9. State durable rules at the highest useful level. Do not add obvious prohibitions, near-duplicate warnings, or case-by-case exclusions.
10. Treat examples, bad outputs, and edge cases as test evidence. Include only the minimum labeled example needed to define a reusable boundary; explicit rules remain authoritative.
11. For Python f-strings, escape literal JSON braces as `{{` and `}}`; real interpolation placeholders stay single-braced, such as `{image_width}`.
12. Apply the owning language's bounded Quick Check before presentation: a smallest safe local smoke for light code, or syntax plus changed prompt variable/constant and direct-reference checks for heavy/API paths. Do not run external prompt trials in Quick Check.
13. Present `CODE READY` with Quick Check evidence, then create a separate `End Task-{concise related task name}` thread and return without waiting. In that Ending thread, test the prompt with representative input/output scenarios. Use repeated fresh runs for stochastic production prompts: default 3 and 5 for critical image, structured-data, or reliability claims. Report artifact creation separately from semantic/file/visual acceptance, and reopen with a corrected prompt if validation fails.

## Function Prompt Shape

```python
prompt = f"""
Objective:
Extract <target> from <source>.

Context and inputs:
- SOURCE_TEXT contains <source role>.

Requirements:
- <required behavior>

Constraints:
- <hard boundary or missing-value behavior>

Output contract:
Return only valid JSON matching this schema:
{{
  "<key>": "<value>"
}}

Success criteria:
- <measurable acceptance condition>

Failure conditions:
- <observable rejection condition>

Verification:
- Check <semantic and structural evidence> before returning.

<SOURCE_TEXT>
{source_text}
</SOURCE_TEXT>
"""
```

## Human-Reading Content Prompt Shape

```python
prompt = f"""
Role:
<only when a domain perspective changes the content>

Objective:
Write <content type> for <audience/use case> from <source/input>.

Context and inputs:
- <source role, audience, environment, or limitation>

Requirements:
- Emphasize <most important qualities> first.

Constraints:
- <hard boundary>

Output contract:
<exact content format and measurable length>

Success criteria:
- <observable audience/content requirement>

Failure conditions:
- <observable rejection condition>

Verification:
- Check <required facts, coverage, and format> before returning.

<SOURCE>
{source_text}
</SOURCE>
"""
```

## Guardrails

- Do not add persona text such as `You are...` unless a domain perspective or responsibility materially changes the result.
- Let the output schema define the container shape and fields instead of repeating verbose JSON warnings.
- Do not add sibling-case warnings for cases the user did not mention.
- Do not add obvious prohibitions that already follow from the objective, requirements/constraints, or output contract.
- Do not add vague filler such as "be accurate" when a concrete rule can say what accuracy requires.
- Do not use blanket `ask instead of guess`, maximum reasoning, long responses, mandatory visible planning, or many few-shot examples. Define the bounded behavior that the task actually needs.
- Use named delimiters when executable prompt strings contain multiple source blocks, examples, or instruction/data boundaries; state each block's role.
- Request concise rationale, evidence, or checks when needed, never private chain-of-thought.
- Do add necessary logic when the prompt lacks it. Do not keep adding repeated prompt rules to cover every observed failure; replace the weak block with a complete working rule that matches the prompt goal.
- Return the optimized Python assignment or C# constant directly when the user asks for prompt code only.

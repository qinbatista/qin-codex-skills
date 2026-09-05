# Prompts in Code

Use [Prompt Skill](../../prompt-skill/SKILL.md) for prompt design and the owning language reference for executable syntax. This file adds only string integration details.

- Keep durable instructions separate from per-run values; pass values through explicit placeholders or named data blocks.
- A compact function prompt states the objective and input roles, necessary rules, the return contract, and a before-returning check when useful. Use headings or a role only when they clarify the task.
- Let an enforced response schema define structure instead of repeating JSON-format warnings.
- Python f-strings escape literal JSON braces as `{{` and `}}`; real placeholders remain single-braced, such as `{source_text}`.
- Use the C# string form supported by the project's actual language version. Preserve interpolation and escaping deliberately.
- Check the changed string, placeholders, direct consumers, and representative output in the active task. Use a local fixture when it proves the behavior; run a provider trial only when that output behavior is part of the requested scope. Do not defer validation to Ending.

```python
prompt = f"""
Extract <fields> from SOURCE. Use null for unavailable values.
Return only the object defined by the response schema.
<SOURCE>
{source_text}
</SOURCE>
""".strip()
```

The example illustrates shape, not mandatory wording. Return the assignment or constant directly when the user asks for prompt code only.

# Spark Code Route

Follow `workflow-skill` as the authority for model assignment. When its `Models by phase` contract assigns Python/C# code writing, editing, debugging, test-code writing, or small code probes/tests to Spark, use `GPT-5.3-Codex-Spark` (`gpt-5.3-codex-spark`) for that phase unless `workflow-skill`'s protected fallback visibly switches the phase to `GPT-5.5` light (`gpt-5.5`, low effort).

For standalone small obvious Python/C# tasks where `workflow-skill` has not provided a model phase table, Spark remains the preferred route when an allowed model-selection or delegation route exists.

## Use When

Use this reference when either condition is true:

- `workflow-skill` assigned the current Python/C# code or code-test phase to Spark.
- The task is a standalone optional Spark candidate that meets every low-risk condition below.

The optional-route constraints below do not override `workflow-skill`'s forced model assignment.

- The request is clearly bounded and affects one or a few files.
- The expected edit, cleanup, review target, or verification path is obvious from the request or shallow inspection.
- The requested code language is Python or C#.
- The task does not require deep debugging, architecture changes, security-sensitive reasoning, migrations, or broad repository archaeology.
- Verification is simple, such as a focused lint, test, build, type check, or direct file inspection.

## Model Names

```text
GPT-5.3-Codex-Spark
gpt-5.3-codex-spark
GPT-5.5 light fallback
gpt-5.5 with low reasoning effort
```

If no allowed Spark route exists in the current environment, continue with the current model and mention that limitation only when it matters. Spark never bypasses project rules, language rules, or final review.

If `workflow-skill` explicitly requires Spark for the current code/test phase and Spark cannot be reached, do not use an unnamed fallback. Use only the protected `GPT-5.5` light fallback when `workflow-skill` has displayed `Model switch: Spark -> GPT-5.5 light` with the reason, or mark the phase blocked/ask for user direction when that fallback is also unavailable.

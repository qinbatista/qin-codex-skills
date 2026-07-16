# Priority-First Code Production

Eligible text-only code producers use the optional priority producer generated from the current Codex catalog. Today that role resolves to `gpt-5.3-codex-spark`: `low` for easy work and `high` for complex work. The role is catalog-derived, so replacement or removal of Spark does not break the quality ladder.

The priority producer stays outside schema-version-2 plan nodes. The dispatcher injects it as the receipt-backed first attempt while the plan's selected catalog quality pair remains the fallback.

A zero-result, zero-token access/launch/transport failure may immediately try that quality pair. Once the priority producer publishes a result, foreground fallback stops. Ending correctness/quality failure is written to the matching Obsidian project/task/module/file/symbol/code context before a new quality-pair repair lifecycle and a different verifier. `code-skill` ownership remains mandatory.

A model label or cached capability is not execution proof. Require one route receipt containing every attempt and its sanitized `model_learning_context`. Start Ending with `--producer-receipt`; the terminal lifecycle event records the outcome automatically. Old local `model_experience.json` remains legacy read-only. Present the completed result first; Ending Real runs independently and a different Ending verifier confirms any repair.

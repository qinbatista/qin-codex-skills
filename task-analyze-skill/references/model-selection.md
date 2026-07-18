# Catalog-Generated Model Selection

The shared source of truth is the saved `assets/model-capability-ladder.json`. Ordinary routing loads it without comparing or refreshing the local catalog. If the ladder is missing, `scripts/model_registry.py` may bootstrap it once from `~/.codex/models_cache.json` without network access. Only an explicit user model-update request may run `scripts/sync_model_capabilities.py` to rescan the local cache and replace the ladder. If that cache is unavailable, retain the last valid ladder. `--check` verifies the saved JSON and human snapshot agree; it does not update either file.

## Quality Order

The saved quality ladder contains only the highest numeric GPT family seen during the last explicit local update, excluding the optional priority producer. Provider catalog priority orders that family's variants from weakest to strongest, and each variant contributes only its supported reasoning efforts. Older numeric families remain catalog-only.

`low -> medium -> high -> xhigh -> max -> ultra`

Only efforts exposed for a model are included. Movement stays inside the generated pairs:

- Real PASS trials one lower effort on the same model, then the strongest effort on the next weaker model.
- Quality/correctness failure trials one higher effort on the same model, then the lowest effort on the next stronger model.
- Repeated PASS freezes the generated minimum pair; an adjacent verified pass/fail boundary also freezes its lowest passing pair.
- Operational failure is quality-neutral.

## Cold Start And Priority Producer

Cold starts are derived from three catalog roles instead of versioned names: weakest, balanced, and frontier. Each task type maps easy/complex work to one of those roles and the closest supported effort.

The catalog may also expose an optional specialized priority text/code producer. The current catalog resolves that role to Spark, so easy work uses low effort and complex work uses high effort. It remains outside the quality ladder. A zero-result, zero-token operational failure may use the contextual quality pair; a published result never foreground-fallbacks. Ending quality/correctness failure is recorded before a new quality-pair repair lifecycle.

## Learning Boundary

Every eligible production task runs `obsidian_adaptive_model_runner.py`, including a cold context. The runner reads the generated ladder and matching Obsidian broad `Model Switch.md` context. It produces a receipt but never writes learning.

After presentation, `ending_task_ledger.py start --producer-receipt <path>` binds that receipt to the lifecycle. The terminal Ending event automatically records the matched producer verdict to Obsidian. This closes the former gap where cold-start tasks stayed inline and therefore could never create enough evidence to descend, ascend, or freeze.

Exact read-only, tool-only, image/mixed, verifier, and Ending work stays inline and never fabricates a producer receipt, except that two or three explicit independent read-only source files may use the fixed parallel-source/adaptive-merge schedule. Unavailable or unconfigured Obsidian uses the saved shared cold start without learning and never blocks. The broad project-scoped `Model Switch.md` page is the sole current contextual evidence authority. Open-ended multi-node strategy and every savings claim remain separately performance-admitted.

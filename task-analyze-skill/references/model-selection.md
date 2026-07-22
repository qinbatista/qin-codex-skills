# Catalog-Generated Model Selection

The shared source of truth is the saved `assets/model-capability-ladder.json`. Ordinary routing loads it without comparing or refreshing the local catalog. If the ladder is missing, `scripts/model_registry.py` may bootstrap it once from `~/.codex/models_cache.json` without network access. Only an explicit user model-update request may run `scripts/sync_model_capabilities.py` to rescan the local cache and replace the ladder. If that cache is unavailable, retain the last valid ladder. `--check` verifies the saved JSON and human snapshot agree; it does not update either file.

## Quality Order

The saved quality ladder contains only the highest numeric GPT family seen during the last explicit local update, excluding the optional schedule producer. Provider catalog priority orders that family's variants from weakest to strongest, and each variant contributes only its supported reasoning efforts. Older numeric families remain catalog-only.

`low -> medium -> high -> xhigh -> max -> ultra`

Only efforts exposed for a model are included. Movement stays inside the generated pairs:

- One Real PASS retains the current pair; two receipt-matched Real PASS results trial one lower effort on the same model, then the strongest effort on the next weaker model.
- Quality/correctness failure trials one higher effort on the same model, then the lowest effort on the next stronger model.
- Repeated PASS freezes the generated minimum pair; an adjacent verified pass/fail boundary also freezes its lowest passing pair. When multiple passing pairs share an exact workload hash, rank median logical tokens, then median process time, then weaker rung.
- Operational failure is quality-neutral.

## Cold Start, Score, And Spark Priority

Every submission has a deterministic `0-100` complexity score: `0-24` small, `25-49` standard, `50-74` complex, and `75-100` advanced. An explicit `complexity score: N` or `--complexity-score N` overrides inference. Cold starts are derived from three catalog roles instead of versioned names: weakest, balanced, and frontier. Each task type maps its score band to one of those roles and the closest supported effort.

The catalog may also expose an optional priority producer. The current catalog resolves that role to Spark. A low-risk, low-ambiguity text/code edit scoring `0-24` tries it first; fixed disjoint read-only source branches may also use it. Spark remains outside the quality ladder. Its zero-result, zero-token operational failure falls back to the contextual quality pair. Its Ending correctness/quality failure suppresses Spark for the matching project/task/operation/code-kind/score-band context and upgrades the next matching task to the quality pair. A published result never foreground-fallbacks.

## Learning Boundary

Every eligible production task runs `obsidian_adaptive_model_runner.py`, including a cold context. The runner reads the generated ladder and matching Obsidian broad `Model Switch.md` context. It produces a receipt but never writes learning.

After presentation, `ending_task_ledger.py start --producer-receipt <path>` binds that receipt to the lifecycle. Every lifecycle stores score/band locally. The terminal Ending event automatically records the matched producer verdict, score, switch direction, and next pair to Obsidian. This closes the former gap where cold-start tasks stayed inline and therefore could never create enough evidence to descend, ascend, freeze, or suppress an unsuitable Spark context.

Exact read-only, tool-only, image/mixed, verifier, and Ending work uses `task_complexity_score.py`, reports the score, stays inline, and never fabricates a producer receipt, except that two or three explicit independent read-only source files first cost-admit one contextual producer versus the parallel-source/fused-merge graph. Unavailable or unconfigured Obsidian uses the saved shared cold start without learning and never blocks. The broad project-scoped `Model Switch.md` page is the sole current contextual model evidence authority. Open-ended multi-node strategy and every savings claim remain separately performance-admitted.

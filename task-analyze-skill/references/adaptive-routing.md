# Adaptive Model Learning

The learner chooses a verified contextual `model|effort` boundary for matching project/task/module/file/symbol/code context. Correctness wins over token or time savings.

## Two Routing Authorities

- Shared: saved `assets/model-capability-ladder.json` contains the last explicitly refreshed local Codex model order, supported efforts, source digest, cold starts, schedule-producer policy, and movement rules, with no user history.
- Project scoped: Obsidian broad `Model Switch.md` pages contain receipt-backed contextual evidence keyed by project/task/module/file/symbol/code fields.

The shared registry may be atomically bootstrapped from the local cache when missing. Ordinary tasks never refresh it. Only an explicit user model-update request may rescan the local cache and replace a valid registry; this workflow never fetches over the network. If the cache is unavailable, preserve the last valid registry. If both are absent, routing fails clearly instead of inventing models.

## Start And End Flow

1. Every eligible text/code production task reads the generated registry and its matching Obsidian context.
2. The contextual quality pair runs directly. A cold context is a real producer route rather than an inline dead end; the optional fast producer is schedule-only for disjoint source branches.
3. A zero-result, zero-token operational failure may run one stronger quality pair in the same receipt.
4. The result is presented immediately.
5. The lifecycle starts with `--producer-receipt`; its Ending PASS/FAIL event automatically writes the producer outcome to Obsidian.
6. The next matching task moves exactly one rung, freezes a verified floor/boundary, or reuses a frozen pair.

The automatic Ending write stores sanitized model/effort, quality verdict, task context, tokens, timing, and receipt hash on the existing broad page. Project, task, module, file, symbol, and code remain record fields; no hierarchy notes are created. It never stores raw prompts, raw results, credentials, or secrets. A verifier pair is never learned as the producer.

Each terminal write rebuilds the six sections on that same broad `Model Switch.md` page. Categories are exactly `normal-script-update`, `code-design`, `finding-bugs`, `tests-verification`, `documentation-instructions`, and `general-work`; public `switch_direction` values are exactly `initial`, `upgrade`, `downgrade`, `freeze`, `no_switch`, and `operational_fallback`. The initial attempt is displayed separately from quality-ladder movement.

## Movement

- First PASS at a pair: retain it and collect evidence. Second PASS at that pair: one rung down, effort before model.
- Quality/correctness FAIL: one rung up, effort before stronger model; record the failure before repair.
- Operational FAIL: neutral; it does not create a quality boundary.
- Like-for-like passing pairs: median tokens first, median process time second, weaker rung third.
- Lowest passing pair or closed pass/fail boundary: freeze with `trial=false` until a later quality failure or catalog/policy drift.

Evidence never crosses project keys merely because two tasks share a broad page or display name. The broad `Model Switch.md` page is the sole active private authority. `strategy_performance.py` remains the separate authority for multi-node Global-versus-Direct admission and savings claims.

An unavailable vault or unregistered project owner disables private learning but does not disable execution. The runner uses the shared cold-start pair and marks `memory_available=false`; dispatcher proof uses `selection_basis=shared_cold_start`. A read-only list of two or three independent project-relative sources first cost-admits a single contextual quality producer versus a graph from source byte metadata. Only context pressure or an explicit latency contract admits schedule-producer branches plus an adaptive merge. Exact-owned three-source graphs fuse the final source audit into that merge; other graphs use a dependency-results-only merge. Exact-expression or dependency-coupled work remains one producer. Open-ended graphs and public savings claims still require `strategy_performance.py` evidence.

# Adaptive Model Learning

The learner chooses a verified contextual `model|effort` boundary for matching project/task/module/file/symbol/code context. Correctness wins over token or time savings.

## Two Routing Authorities

- Shared: saved `assets/model-capability-ladder.json` contains the last explicitly refreshed local Codex model order, supported efforts, source digest, cold starts, optional priority-producer policy, and movement rules, with no user history.
- Project scoped: Obsidian broad `Model Switch.md` pages contain receipt-backed contextual evidence keyed by project/task/module/file/symbol/code fields.

The shared registry may be atomically bootstrapped from the local cache when missing. Ordinary tasks never refresh it. Only an explicit user model-update request may rescan the local cache and replace a valid registry; this workflow never fetches over the network. If the cache is unavailable, preserve the last valid registry. If both are absent, routing fails clearly instead of inventing models.

## Start And End Flow

1. Every eligible text/code production task reads the generated registry and its matching Obsidian context.
2. The optional priority producer runs first; otherwise the contextual quality pair runs directly. A cold context is a real `trial=true` producer route rather than an inline dead end.
3. A zero-result, zero-token priority-producer operational failure may run the contextual quality fallback in the same receipt.
4. The result is presented immediately.
5. The lifecycle starts with `--producer-receipt`; its Ending PASS/FAIL event automatically writes the producer outcome to Obsidian.
6. The next matching task moves exactly one rung, freezes a verified floor/boundary, or reuses a frozen pair.

The automatic Ending write stores sanitized model/effort, quality verdict, task context, tokens, timing, and receipt hash on the existing broad page. Project, task, module, file, symbol, and code remain record fields; no hierarchy notes are created. It never stores raw prompts, raw results, credentials, or secrets. A verifier pair is never learned as the producer.

Each terminal write rebuilds the six sections on that same broad `Model Switch.md` page. Categories are exactly `normal-script-update`, `code-design`, `finding-bugs`, `tests-verification`, `documentation-instructions`, and `general-work`; public `switch_direction` values are exactly `initial`, `upgrade`, `downgrade`, `freeze`, `no_switch`, and `operational_fallback`. The priority attempt is displayed separately from quality-ladder movement.

## Movement

- PASS: one rung down, effort before model.
- Quality/correctness FAIL: one rung up, effort before stronger model; record the failure before repair.
- Operational FAIL: neutral; it does not create a quality boundary.
- Priority-producer quality FAIL: record first, then start a new repair lifecycle on the contextual quality pair.
- Lowest passing pair or closed pass/fail boundary: freeze with `trial=false` until a later quality failure or catalog/policy drift.

Evidence never crosses project keys merely because two tasks share a broad page or display name. The broad `Model Switch.md` page is the sole active private authority. `strategy_performance.py` remains the separate authority for multi-node Global-versus-Direct admission and savings claims.

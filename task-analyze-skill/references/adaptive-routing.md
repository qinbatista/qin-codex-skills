# Adaptive Model Learning

The learner chooses a verified contextual `model|effort` boundary for matching project/task/module/file/symbol/code context. Correctness wins over token or time savings.

## Two Routing Authorities

- Shared: saved `assets/model-capability-ladder.json` contains the last explicitly refreshed local Codex model order, supported efforts, source digest, cold starts, schedule-producer policy, and movement rules, with no user history.
- Project scoped: Obsidian broad `Model Switch.md` pages contain receipt-backed contextual evidence keyed by project/task/module/file/symbol/code fields.

The shared registry may be atomically bootstrapped from the local cache when missing. Ordinary tasks never refresh it. Only an explicit user model-update request may rescan the local cache and replace a valid registry; this workflow never fetches over the network. If the cache is unavailable, preserve the last valid registry. If both are absent, routing fails clearly instead of inventing models.

## Start And End Flow

1. Every submission and every dynamic graph node receives a deterministic `0-100` score and band. Eligible text/code production also reads the generated registry and its matching Obsidian context.
2. A low-risk, low-ambiguity text/code/write/execute node scoring `0-24` tries Spark first even when its parent task has a higher score. Other nodes run their score role or contextual quality pair directly. Spark may also serve an admitted disjoint source branch.
3. A zero-result, zero-token Spark operational failure may run the contextual quality pair in the same receipt. A quality-pair operational failure may run one stronger quality pair.
4. The result is presented immediately.
5. The hard-required lifecycle starts with score/band and `--producer-receipt` when present; its Ending PASS/FAIL event stores the score locally and automatically writes a receipt-backed producer outcome, switch direction, and next pair to Obsidian.
6. The next matching task moves exactly one rung, freezes a verified floor/boundary, or reuses a frozen pair.

The automatic Ending write stores sanitized model/effort, complexity score/band, quality verdict, task context, tokens, timing, switch direction, next pair, and receipt hash on the existing broad page. Project, task, module, file, symbol, and code remain record fields; no hierarchy notes are created. It never stores raw prompts, raw results, credentials, or secrets. A verifier pair is never learned as the producer.

Each terminal write rebuilds the six sections on that same broad `Model Switch.md` page. Categories are exactly `normal-script-update`, `code-design`, `finding-bugs`, `tests-verification`, `documentation-instructions`, and `general-work`; public `switch_direction` values are exactly `initial`, `upgrade`, `downgrade`, `freeze`, `no_switch`, and `operational_fallback`. The initial attempt is displayed separately from quality-ladder movement.

## Movement

- First PASS at a pair: retain it and collect evidence. Second PASS at that pair: one rung down, effort before model.
- Quality/correctness FAIL: one rung up, effort before stronger model; record the failure before repair.
- Spark quality/correctness FAIL: suppress Spark for the matching project/task/operation/code-kind/score-band context and upgrade the next matching task to its contextual quality pair.
- Operational FAIL: neutral; it does not create a quality boundary.
- Like-for-like passing pairs: median tokens first, median process time second, weaker rung third.
- Lowest passing pair or closed pass/fail boundary: freeze with `trial=false` until a later quality failure or catalog/policy drift.

Evidence never crosses project keys merely because two tasks share a broad page or display name. The broad `Model Switch.md` page is the sole active private authority. `strategy_performance.py` remains the separate authority for multi-node Global-versus-Direct admission and savings claims.

An unavailable vault or unregistered project owner disables private learning but does not disable execution. The runner uses the shared cold-start pair and marks `memory_available=false`; dispatcher proof uses `selection_basis=shared_cold_start`. A structurally valid bounded task graph may execute without performance history. Dependency-ready independent nodes run concurrently; shared-state and output-dependent nodes remain linear. A read-only list of two or three independent project-relative sources retains its source-byte admission and dependency-only-or-fused merge constraints. Public savings claims still require `strategy_performance.py` evidence.

# Runtime Model Receipts

A diagram label or CLI request proves intent only. A useful local receipt combines the request, Codex runtime metadata, token events, and measured elapsed time without storing prompts or secrets.

## Required Fields

- node/workload ID;
- SHA-256 of the prompt, never the raw prompt;
- requested model and effort;
- resolved model and effort from `turn_context`;
- effective model after any `model_reroute` event;
- reroute reason when present;
- thread ID and Codex CLI version;
- input, cached-input, output, reasoning-output, and total tokens;
- model-turn duration, time to first token, and whole-process elapsed time when available;
- sanitized availability metadata such as limit class and whether usable credits were reported, without balances or account identifiers;
- process exit code, match status, and sanitized errors.
- timeout completeness fields: `metrics_complete=false`, measured `process_elapsed_ms`, and `tokens_lower_bound=true` only when partial rollout usage exists.
- sanitized node role, entry-context status, and authorization source; never the environment or marker value.

Do not save raw stdout, stderr, prompts, response items, base instructions, environment, auth data, rate limits, credits, or rollout summaries.

## Entry-Context Authorization

`model_execution_receipt.py --entry-task` gives the spawned Codex controller an inherited entry-context marker. While that marker is present, a result producer needs either `adaptive_model_runner.py` in-process authorization or the dispatcher's distinct adaptive-result authorization after a fresh learner recommendation exactly matches the locked pair, trial flag, fingerprint, and proof. A plain fixed-pair or forged dispatcher receipt call is rejected before `codex exec`. Dispatcher verification, repair, and ending nodes have separate matching in-process authorization. Role labels alone are insufficient. Fixed-pair benchmark baselines work outside entry context and cannot be used as an entry fallback.

When an orchestrating parent needs the routed node's user-facing result, `model_execution_receipt.py run --result-output <task-cache-path>` may save only the final agent message in the active task cache. The sanitized receipt stores its hash and path, never raw stdout/stderr.

On timeout, preserve the prompt/workload hashes, measured elapsed time, partial thread identity, resolved/effective pair, last allowlisted token count, and availability when recoverable. Partial tokens are a lower bound, never a completed-run total. Do not replace recoverable evidence with an empty generic receipt.

## Local Evidence Level

`codex exec --json` provides thread and token events, but not resolved model/effort by itself. A persistent run can be joined to `~/.codex/state_5.sqlite`, and its rollout can be allowlist-parsed for `turn_context`, `model_reroute`, `token_count`, and `task_complete` fields.

This is strong operational evidence from the local Codex runtime. It is not a cryptographically signed backend attestation. State that limitation exactly; do not overclaim.

## Savings Comparison

Use a like-for-like comparison: compare the designed downstream route with a leakage baseline where the same downstream nodes are forced to the entry model/effort. Hold prompts, inputs, topology, cwd, sandbox, output contract, and acceptance criteria constant.

To bypass only Task Analyze, run the baseline as a bounded `LOCKED_ROUTE_NODE` on the entry pair while keeping the same user/project configuration. `--ignore-user-config` changes more than routing and is not a fair strategy baseline. Aggregate each unique entry/child/dispatcher/collaboration session exactly once. Report time/tokens to Mini-passed first result separately from optional Ending totals.

Compare `workload_prompt_sha256`, which hashes the bounded task prompt before route markers are added. Do not compare wrapper-level prompt hashes; execution wrappers may differ even when the real workload is identical.

- Cached input is part of input tokens; do not add it again.
- Reasoning output is part of output tokens; do not add it again.
- For sequential work, sum elapsed time.
- For parallel work, compare scheduler critical-path elapsed time, not the sum of branch durations.
- One pair is a smoke result. Prefer alternating order and median of at least three runs for a durable claim.

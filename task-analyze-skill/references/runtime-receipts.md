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

Do not save raw stdout, stderr, prompts, response items, base instructions, environment, auth data, rate limits, credits, or rollout summaries.

When an orchestrating parent needs the routed node's user-facing result, `model_execution_receipt.py run --result-output <task-cache-path>` may save only the final agent message in the active task cache. The sanitized receipt stores its hash and path, never raw stdout/stderr.

## Local Evidence Level

`codex exec --json` provides thread and token events, but not resolved model/effort by itself. A persistent run can be joined to `~/.codex/state_5.sqlite`, and its rollout can be allowlist-parsed for `turn_context`, `model_reroute`, `token_count`, and `task_complete` fields.

This is strong operational evidence from the local Codex runtime. It is not a cryptographically signed backend attestation. State that limitation exactly; do not overclaim.

## Savings Comparison

Use a like-for-like comparison: compare the designed downstream route with a leakage baseline where the same downstream nodes are forced to the entry model/effort. Hold prompts, inputs, topology, cwd, sandbox, output contract, and acceptance criteria constant.

Compare `workload_prompt_sha256`, which hashes the bounded task prompt before route markers are added. Do not compare wrapper-level prompt hashes; execution wrappers may differ even when the real workload is identical.

- Cached input is part of input tokens; do not add it again.
- Reasoning output is part of output tokens; do not add it again.
- For sequential work, sum elapsed time.
- For parallel work, compare scheduler critical-path elapsed time, not the sum of branch durations.
- One pair is a smoke result. Prefer alternating order and median of at least three runs for a durable claim.

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
- for an adaptive producer only, one sanitized `model_learning_context` with project root, task/module/file/symbol/code/operation, modality, complexity, risk, ambiguity, and bounded task summary; no raw prompt or result.

Do not save raw stdout, stderr, prompts, response items, base instructions, environment, auth data, rate limits, credits, or rollout summaries.

## Entry-Context Authorization

`model_execution_receipt.py --entry-task` gives the spawned Codex controller an inherited entry-context marker. While that marker is present, an ordinary result producer needs `obsidian_adaptive_model_runner.py` in-process authorization after the current Obsidian project-context recommendation selects the exact shared-ladder pair; a multi-node dispatcher uses its distinct adaptive-result authorization after the locked recommendation matches its pair, trial flag, fingerprint, and proof. The old `adaptive_model_runner.py` authorization is legacy compatibility only. A plain fixed-pair or forged dispatcher receipt call is rejected before `codex exec`. Dispatcher verification, repair, and ending nodes have separate matching in-process authorization. Role labels alone are insufficient. Fixed-pair benchmark baselines work outside entry context and cannot be used as an entry fallback.

When an orchestrating parent needs the routed node's user-facing result, `model_execution_receipt.py run --result-output <task-cache-path>` may save only the final agent message in the active task cache. The sanitized receipt stores its hash and path, never raw stdout/stderr.

After that result is shown, start Ending with `ending_task_ledger.py start --producer-receipt <receipt-path>`. The ledger validates and privately binds the learning context. A producer-bound `event pass` writes the matched Obsidian Model Switch record before terminal PASS; a producer-bound `event fail --failure-class <class>` writes lifecycle FAIL first and then the failed model outcome. Lifecycles without a producer receipt keep the ordinary non-learning behavior. Duplicate receipt/verdict records are idempotent success.

On timeout, preserve the prompt/workload hashes, measured elapsed time, partial thread identity, resolved/effective pair, last allowlisted token count, and availability when recoverable. Partial tokens are a lower bound, never a completed-run total. Do not replace recoverable evidence with an empty generic receipt.

## Local Evidence Level

`codex exec --json` provides thread and token events, but not resolved model/effort by itself. A persistent run can be joined to `~/.codex/state_5.sqlite`, and its rollout can be allowlist-parsed for `turn_context`, `model_reroute`, `token_count`, and `task_complete` fields.

This is strong operational evidence from the local Codex runtime. It is not a cryptographically signed backend attestation. State that limitation exactly; do not overclaim.

## Savings Comparison

Use a like-for-like comparison between the exact raw task on the user's current model and the same raw task with the hookless Global bootstrap active. Hold prompt, inputs, cwd, sandbox, user/project configuration, output contract, acceptance criteria, and execution order constant. A routed Global arm must additionally count its complete entry/controller and descendant path.

Run the Direct arm through `model_execution_receipt.py run --direct-task --benchmark-run-id benchmark-<run-id>` and pass the exact raw task prompt over stdin. Run the Global arm through `--bootstrap-task --benchmark-run-id benchmark-<run-id>` with the same raw prompt and the production bootstrap in its isolated `CODEX_HOME/AGENTS.md`. Both modes intentionally add no `LOCKED_ROUTE_NODE`, run outside Task Analyze entry context, and use `result-producer`; `direct-task` versus `bootstrap-task` plus the frozen AGENTS hash proves the arm. Reserve `--entry-task` for a real full Task Analyze entry. Keep the same user/project configuration; `--ignore-user-config` changes more than routing and is not a fair strategy baseline. Aggregate each unique foreground root and descendant session exactly once. End user-visible time when the completed result first appears; exclude Ending/verification roots and their descendants from task token/time cost and report them separately as diagnostics. The receipt runner flushes one sanitized `result-ready` event immediately after the atomic result write; the benchmark controller stamps that event in its own monotonic clock, stores the child-local monotonic value only as a diagnostic, and binds the runner-owned timestamp exactly across evidence and receipt.

Every formal cohort freezes the complete model-visible environment before the plan is written. Each arm uses real suite-local `skills/` and `plugins/` directories, suite-local marketplace roots, copied model/memory snapshots, byte-identical `config.toml`, and immutable catalog files; only the Direct empty AGENTS versus Global production bootstrap may differ. Never symlink a benchmark catalog to live `~/.codex` or another mutable cache. Prewarm plugin discovery without model traffic, compare normalized discovery plus catalog hashes, and validate the environment immediately before every arm. Any skills/plugin/marketplace/config/memory drift invalidates the cohort as an operational failure and cannot be resumed or learned as model quality.

The benchmark gate must reject the wrong node type, active entry context, wrong authorization source, mismatched `benchmark_run_id`, mismatched workload ID, or any difference between raw `prompt_sha256` and `workload_prompt_sha256`. A mode label without those bindings is not proof.

Compare `workload_prompt_sha256`, which hashes the bounded task prompt before route markers are added. Do not compare wrapper-level prompt hashes; execution wrappers may differ even when the real workload is identical.

End-to-end strategy comparison aggregates every unique foreground session and attempt once. After at least six comparable pairs, logical tokens require lower Global cohort totals/raw medians and a non-negative paired-savings median; pairwise wins and individual regressions remain diagnostics instead of arbitrary percentage vetoes. Simple first-result performance must stay inside the Direct cohort's measured median-absolute-deviation noise envelope. Medium requires lower totals/raw medians, non-negative paired savings, and a strict majority of faster pairs. Complex time is diagnostic and cannot veto a correct token-saving cohort. Continue optimization only while a reproducible deterministic waste source remains; stop when repeated evidence is noise-bound or no correctness-preserving change remains. Ending/verification tokens and total-wall time are diagnostic only. The benchmark receipt worker emits one flushed result-ready event immediately after the atomic result write; the parent runner stamps that event on its own monotonic clock, so file polling, receipt finalization, telemetry, and Ending do not extend first-result time. `benchmark_suite_gate.py` derives acceptance from raw result/evidence/receipts; manifests may not supply their own pass status. Before publication, `benchmark_public_export.py` re-evaluates every run from the raw files and exact-matches the regenerated manifests and summary; missing, stale, or tampered raw evidence fails closed.

- Cached input is part of input tokens; do not add it again.
- Reasoning output is part of output tokens; do not add it again.
- For sequential work, sum elapsed time.
- For parallel work, compare scheduler critical-path elapsed time, not the sum of branch durations.
- One pair is a smoke result. Prefer alternating order and median of at least three runs for a durable claim.

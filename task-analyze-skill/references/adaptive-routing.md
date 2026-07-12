# Private Adaptive Routing

## Purpose

Learn Qin's best downstream model and effort per sanitized task profile from real execution receipts plus independent verification. The goal is correctness first, then like-for-like optimization evidence after correctness gates are met—not expensive models by default and not Task Analyze intuition alone. Receipt timing/tokens cannot bypass quality boundaries. A rung is a complete `model_name|effort` pair on a weak-to-strong quality ladder; cross-model movement is not assumed to be cheaper.

## Storage

- Ledger: `task-analyze-skill/local/adaptive-routing/model_experience.json` (generated locally when missing)
- Owner: `task-analyze-skill`
- Recorder/status route: `management-skill`
- Selection route: `task-analyze-skill`

The `local/` subtree is personal state. Mirror snapshots, hashes, safety scans, diffs, sync, and push exclude it. Pull preserves it byte-for-byte.

End-to-end delegation performance is stored separately in `local/adaptive-routing/strategy_performance.json` through `scripts/strategy_performance.py`. Quality/capability learning remains entry-independent; performance admission is keyed by profile fingerprint, current entry pair, configuration cohort, sandbox, strategy version, producer-contract version, and exact workload hash because controller overhead changes with those values.

Obsidian `TaskModelExperience/` is an optional sanitized readable projection for Task Analyze and other skills. It never replaces this private ledger as the machine selection authority. Write it only in Ending Task after Real Verify; if Obsidian is unavailable, skip the projection without affecting routing.

## Sanitized Profile

Each local condition record has only controlled profile values: task family, artifact, `execution_domain`, scope, ambiguity, modality, risk, complexity, owning skill, project family, and verification shape. The domain is part of identity, so Python, plain C#, Unity C#, and non-code evidence do not share calibration. It also has a canonical candidate ladder, static suggestion, hard floor, one generalized privacy-filtered task summary, and explicit `success_model`/`failed_model` ranges.

Its attempt rows retain only a sanitized route-run ID, producer pair, receipt/proof fields, Ending Real outcome, allowlisted failure class, trial flag, prompt-free `workload_prompt_sha256`, token totals, process time, and recording time. Never store raw prompts, raw results, paths, filenames, repository names, thread/session IDs, raw errors, account data, environment, auth data, secrets, or other private task content.

## Event Evidence

A result-producer attempt may contain requested/resolved/effective model and effort, receipt status, Ending Real verdict, allowlisted failure class, prompt-free workload hash, token counts, process time, trial status, and a sanitized route-run ID. Ending Real creates or updates that producer attempt and never records the verifier model as the result producer.

`receipt_status=pass` requires a completed turn plus matching model and effort. Missing or mismatched receipts cannot earn a successful sample. No foreground provisional verdict is recorded.

## Recommendation Policy

Task Analyze supplies one stable profile preset plus only its required project/owner/domain values. The preset registry derives the weak-to-strong quality ladder, static baseline, hard floor, and controlled condition fields. The entry model is not an input, and callers never serialize the ladder.

For every non-tiny model profile, the supplied ladder is exactly the complete supported GPT-5.6 Luna/Terra/Sol ladder, not a fixed category pair and not truncated by its hard floor. An eligible tiny profile prepends Spark-low to that full normal fallback ladder; no other Spark effort is allowed.

Calibration is a bounded search for the best complete `model|effort` pair for one exact sanitized task profile. Profiles are exact across every controlled condition field, including execution domain; evidence from Python, Unity C#, another project family, or another verification shape does not calibrate this profile.

1. Resolve the owning skill and `execution_domain`, then apply supported-input, supported-effort, safety, authority, project, language, code-style, and owning-skill floors.
2. With no prior success, use the static suggestion. The sole automatic exception is safe low-risk text-only tiny text/code/command work, which starts at eligible Spark-low.
3. A runtime Spark failure for that exception uses the static suggestion without a quality penalty. Result execution retries only the exact planned `model|effort` fallback pairs and keeps sanitized attempt evidence; Ending verdict failures do not model-retry.
4. After a receipt-matched pass, trial exactly one lower eligible rung: lower effort on the same model first; only after that model reaches its minimum eligible effort, trial the next weaker model at that model's highest eligible effort. The normal ladder is Luna low (also called “light”) through Luna efforts, Terra efforts, then Sol ultra; Spark-low is only the tiny-work exception.
5. Ending Real updates the same producer receipt/run, recomputes the recommendation, and persists/freezes `best_pair` once adjacent Real-verified pass/fail evidence identifies the eligible pair or a Real pass proves the hard floor. Reuse the frozen exact-profile `selected_pair` with `trial=false` until verified failure, ladder/hard-floor/profile drift, policy change, or explicit reset.
6. Reopen the bounded search only for a receipt-matched Ending Real correctness/quality failure, material profile drift, policy or eligible-ladder/hard-floor change, or explicit reset. On quality failure, upgrade in exact reverse order: raise effort on the same model first, then move to the next stronger eligible model only after the current model's eligible efforts are exhausted. When no stronger candidate exists, return a blocked/exhausted recommendation with no selected pair.
8. Availability, timeout, protocol, telemetry, execution, or receipt failures, plus unverified or mismatched receipts, are temporary diagnostic evidence. They can block pass credit or use an allowed execution fallback, but they never move the learned quality best or either quality boundary.
9. An attempt-level quality failure cannot be erased by a later pass under the same route-run ID. A genuine retry gets a new route-run ID so both samples remain auditable.
10. High-risk or irreversible work records evidence but does not auto-downgrade.

Correctness/quality is the eligibility gate. Cost evidence is comparable only when at least two Real-passing pairs share an exact `workload_prompt_sha256` cohort and every compared pair has complete tokens and time. The recorder equal-weights shared cohorts, then minimizes median total tokens first, median process time second, and weaker rung last. Different workload hashes, missing hashes, incomplete metrics, or one passing pair fall back to the verified quality boundary and cannot support a savings claim. Tokens are a usage proxy, not a dollar-cost claim.

Producer cost ranking never admits delegation by itself. The separate strategy gate requires at least six end-to-end Direct/Global pairs for the exact workload and entry/configuration cohort. Every arm must pass correctness with complete metrics and no retry/fallback/repair/unreceipted session. Logical tokens require lower Global cohort totals/raw medians and non-negative paired-median savings; pairwise wins and individual regressions are diagnostics. First-result latency requires lower Global cohort totals/raw medians, non-negative paired-median savings, and a strict majority of faster pairs. Ending/total-wall time is diagnostic and excluded from user-visible latency. Optimization continues only while repeated evidence identifies a deterministic correctness-preserving improvement; noise-bound comparisons stop the search. Foreground calibration is forbidden; explicit benchmark calibration is the only bypass.

## Profile Presets

Use `model_routing_history.py profiles` to inspect the stable registry. Built-in presets cover grounded repository answers at easy/complex scope, tiny text, command generation, tiny code, and easy/complex code. `tiny-code`, `code-easy`, and `code-complex` require one active code `--execution-domain`; the registry automatically supports Python, C#, Unity C#, and future active code domains without duplicating preset rows.

Classify by requested output. Reading Python or Unity C# to reconstruct and explain a repository workflow is `grounded-repository-answer-easy` or `grounded-repository-answer-complex` with `execution_domain=general` and the owning project skill. It is not a code preset unless the task creates, changes, executes, or validates code as code.

The calibrated MuseAI complex profile is addressed without a ladder:

```bash
python3 scripts/model_routing_history.py recommend --profile-preset grounded-repository-answer-complex --project-family museai --owning-skill muse-ai-plugin:muse-ai-dev-skill --task-summary "Reconstruct a bounded repository workflow and return verified structured evidence."
```

This resolves the exact explicit condition `grounded/answer/multi/low/text/low/complex/museai/real/muse-ai-plugin:muse-ai-dev-skill/general`, the full normal ladder, Terra-high static suggestion, and Luna-low hard floor. `adaptive_model_runner.py` accepts the same concise profile arguments and owns selection plus receipt execution, then emits the completed result without foreground verification. Ending Real owns the grounded gate and quality recording. Do not pass `--candidate-ladder`, `--static-suggestion`, or `--hard-floor` from the entry.

For JSON results, `--grounded-gate-preset json-object` checks receipt binding and exact JSON. `grounded-source-json-v1` additionally requires sorted contained `source_files`. `workflow-graph-json-v1` preserves the legacy six-key workflow contract with `public_return_keys`. `workflow-graph-json-v2` uses `always_return_keys` plus `optional_return_keys`, so conditional output and `conditional_serial` stage contracts do not have to be flattened into inaccurate parallel/serial claims. Both workflow presets sort agent/file/field lists while preserving dependency and early-exit order. Source-aware presets also take `--grounded-source-root`. Use the strict config file only for a different declared schema.

Use `recommend` and `record` with `--profile-preset`, `--project-family`, generalized `--task-summary`, and only the owner/domain values required by that preset. Migrate old missing domain values as:

- `code_unspecified` for legacy code evidence.
- `general` for non-code evidence.

`record` takes the main producer `--receipt`, `--verify-level real`, `--verify-status`, and the same sanitized `--run-id` after Ending Real. Direct non-dispatch model routes invoke it too; tool-only routes never record adaptive producer samples.

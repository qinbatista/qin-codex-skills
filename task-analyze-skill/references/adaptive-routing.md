# Private Adaptive Routing

## Purpose

Learn Qin's best downstream model and effort per sanitized task profile from real execution receipts plus independent verification. The goal is correctness first, then like-for-like optimization evidence after correctness gates are met—not expensive models by default and not Task Analyze intuition alone. Receipt timing/tokens cannot bypass quality boundaries. A rung is a complete `model_name|effort` pair on a weak-to-strong quality ladder; cross-model movement is not assumed to be cheaper.

## Storage

- Ledger: `task-analyze-skill/local/adaptive-routing/model_experience.json` (generated locally when missing)
- Owner: `task-analyze-skill`
- Recorder/status route: `management-skill`
- Selection route: `task-analyze-skill`

The `local/` subtree is personal state. Mirror snapshots, hashes, safety scans, diffs, sync, and push exclude it. Pull preserves it byte-for-byte.

## Sanitized Profile

Each local condition record has only controlled profile values: task family, artifact, `execution_domain`, scope, ambiguity, modality, risk, complexity, owning skill, project family, and verification shape. The domain is part of identity, so Python, plain C#, Unity C#, and non-code evidence do not share calibration. It also has a canonical candidate ladder, static suggestion, hard floor, one generalized privacy-filtered task summary, and explicit `success_model`/`failed_model` ranges.

Its attempt rows retain only a sanitized route-run ID, producer pair, receipt/proof fields, Mini/Real outcomes, allowlisted failure class, trial flag, token totals, process time, and recording time. Never store raw prompts, raw results, paths, filenames, repository names, thread/session IDs, raw errors, account data, environment, auth data, secrets, or other private task content.

## Event Evidence

A result-producer attempt may contain requested/resolved/effective model and effort, receipt status, Mini/Real verdict, allowlisted failure class, token counts, process time, trial status, and a sanitized route-run ID. Mini creates or updates that producer attempt; Real updates the same attempt and never records the verifier model as the result producer.

`receipt_status=pass` requires a completed turn plus matching model and effort. Missing or mismatched receipts cannot earn a successful sample.

## Recommendation Policy

Task Analyze supplies a weak-to-strong quality ladder, static baseline, and hard floor. The entry model is not an input.

Calibration is a bounded search for the best complete `model|effort` pair for one exact sanitized task profile. Profiles are exact across every controlled condition field, including execution domain; evidence from Python, Unity C#, another project family, or another verification shape does not calibrate this profile.

1. Resolve the owning skill and `execution_domain`, then apply supported-input, supported-effort, safety, authority, project, language, code-style, and owning-skill floors.
2. With no prior success, use the static suggestion. The sole automatic exception is safe low-risk text-only tiny text/code/command work, which starts at eligible Spark-low.
3. A runtime Spark failure for that exception uses the static suggestion without a quality penalty. Result execution retries only the exact planned `model|effort` fallback pairs and keeps sanitized attempt evidence; Mini/Ending verdict failures do not model-retry.
4. After a receipt-matched verification pass, trial exactly one lower eligible rung: lower effort on the same model first; only after that model reaches its minimum eligible effort, trial the next weaker model at that model's highest eligible effort.
5. Once adjacent receipt-matched pass/fail evidence identifies the selected eligible pair, or a receipt-matched pass proves the current hard floor, derive the calibrated/frozen `selected_pair` from the bounds, reuse it with `trial=false`, and stop searching while trial is closed.
6. Reopen the bounded search only for a receipt-matched Mini or Real correctness/quality failure, material profile drift, policy or eligible-ladder/hard-floor change, or explicit reset. On quality failure, upgrade in exact reverse order: raise effort on the same model first, then move to the next stronger eligible model only after the current model's eligible efforts are exhausted. When no stronger candidate exists, return a blocked/exhausted recommendation with no selected pair.
7. Real Verify failure overrides an earlier Mini pass for the same route-run ID.
8. Availability, timeout, protocol, telemetry, execution, or receipt failures, plus unverified or mismatched receipts, are temporary diagnostic evidence. They can block pass credit or use an allowed execution fallback, but they never move the learned quality best or either quality boundary.
9. An attempt-level quality failure cannot be erased by a later pass under the same route-run ID. A genuine retry gets a new route-run ID so both samples remain auditable.
10. High-risk or irreversible work records evidence but does not auto-downgrade.

Among verified eligible candidates, the recorder uses a correctness boundary and the weakest verified complete pair control anchor. Receipts then provide like-for-like token/time evidence for future optimization. Tokens are a usage proxy, not a dollar-cost claim. `success_model` and `failed_model` are all-history full-pair boundary fields. The recommendation derives `selected_pair` from the active eligible ladder and may differ from historical `success_model` after an eligibility or hard-floor change. Do not claim any field or ranking the recorder does not produce.

## Commands

Use `recommend` and `record` with the complete controlled profile: `--task-family`, `--artifact`, `--execution-domain`, `--scope`, `--ambiguity`, `--modality`, `--risk`, `--complexity`, `--owning-skill`, `--project-family`, `--verification-shape`, generalized `--task-summary`, repeated canonical `--candidate-ladder`, `--static-suggestion`, and `--hard-floor`.
`--execution-domain` is optional. Migrate missing values as:

- `code_unspecified` for legacy code evidence.
- `general` for non-code evidence.

`record` also takes the main producer `--receipt`, `--verify-level`, `--verify-status`, and the same sanitized `--run-id` for Mini then Real. Direct non-dispatch routes invoke it too.

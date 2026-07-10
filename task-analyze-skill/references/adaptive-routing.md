# Private Adaptive Routing

## Purpose

Learn Qin's best downstream model and effort per sanitized task profile from real execution receipts plus independent verification. The goal is correctness first, then fewer tokens and less execution time—not expensive models by default and not Task Analyze intuition alone.

## Storage

- Ledger: `task-analyze-skill/local/adaptive-routing/model_experience.json` (generated locally when missing)
- Owner: `task-analyze-skill`
- Recorder/status route: `management-skill`
- Selection route: `task-analyze-skill`

The `local/` subtree is personal state. Mirror snapshots, hashes, safety scans, diffs, sync, and push exclude it. Pull preserves it byte-for-byte.

## Sanitized Profile

Each local condition record has only controlled profile values: task family, artifact, scope, ambiguity, modality, risk, complexity, owning skill, project family, and verification shape. It also has a canonical candidate ladder, static suggestion, hard floor, one generalized privacy-filtered task summary, and explicit `success_model`/`failed_model` ranges.

Its attempt rows retain only a sanitized route-run ID, producer pair, receipt/proof fields, Mini/Real outcomes, allowlisted failure class, trial flag, token totals, process time, and recording time. Never store raw prompts, raw results, paths, filenames, repository names, thread/session IDs, raw errors, account data, environment, auth data, secrets, or other private task content.

## Event Evidence

A result-producer attempt may contain requested/resolved/effective model and effort, receipt status, Mini/Real verdict, allowlisted failure class, token counts, process time, trial status, and a sanitized route-run ID. Mini creates or updates that producer attempt; Real updates the same attempt and never records the verifier model as the result producer.

`receipt_status=pass` requires a completed turn plus matching model and effort. Missing or mismatched receipts cannot earn a successful sample.

## Recommendation Policy

Task Analyze supplies a cheapest-to-strongest candidate ladder, static baseline, and hard floor. The entry model is not an input.

1. Apply supported-input, supported-effort, safety, authority, project, language, code-style, and owning-skill floors first.
2. With no prior success, use the static suggestion. The sole automatic exception is safe low-risk text-only tiny text/code/command work, which starts at eligible Spark-low.
3. A runtime Spark failure for that exception uses the static suggestion without a quality penalty. Result execution retries only the exact planned `model|effort` fallback pairs and keeps sanitized attempt evidence; Mini/Ending verdict failures do not model-retry.
4. After a receipt-matched verification pass, trial exactly one cheaper/faster candidate: one lower effort on the same model; only after its eligible efforts are exhausted, trial the next weaker eligible model.
5. A Mini or Real correctness or quality failure is sticky: it raises the failed boundary and prevents the failed or weaker rungs from being selected; choose the nearest eligible rung above it. When no stronger current candidate exists, return a blocked/exhausted recommendation with no selected pair.
6. Real Verify failure overrides an earlier Mini pass for the same route-run ID.
7. Availability, timeout, protocol, telemetry, execution, or receipt failures block pass credit but do not become model-quality failures.
8. An attempt-level quality failure cannot be erased by a later pass under the same route-run ID. A genuine retry gets a new route-run ID so both samples remain auditable.
9. High-risk or irreversible work records evidence but does not auto-downgrade.

Among verified eligible candidates, rank correctness first, then median total tokens, then median process time. Tokens are a usage proxy, not a dollar-cost claim.

## Commands

Use `recommend` and `record` with the complete controlled profile: `--task-family`, `--artifact`, `--scope`, `--ambiguity`, `--modality`, `--risk`, `--complexity`, `--owning-skill`, `--project-family`, `--verification-shape`, generalized `--task-summary`, repeated canonical `--candidate-ladder`, `--static-suggestion`, and `--hard-floor`. `record` also takes the main producer `--receipt`, `--verify-level`, `--verify-status`, and the same sanitized `--run-id` for Mini then Real. Direct non-dispatch routes invoke it too.

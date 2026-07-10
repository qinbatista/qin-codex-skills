# Per-Node Model And Effort Selection

Task Analyze runs on the model and effort currently selected at task entry. That pair may be any supported combination and stops being result-bearing authority when the visible route is shown.

## Selection Order

A routing rung is the complete `model_name|effort` pair. This is a weak-to-strong quality ladder, not a price ladder: never assume cross-model means cheaper. To downgrade, move exactly one eligible rung. Lower effort on the same model first; only after that model reaches its minimum eligible effort, move to the next weaker model at that model's highest eligible effort. Upgrade in the exact reverse direction after a Mini or Real correctness/quality failure. Floors always win.

1. During bounded read-only preflight, call `scripts/resolve_entry_model.py` to preserve the current entry pair exactly; use `unverified` only when exact resolution fails. The entry pair is route metadata, never a learning feature.
2. Resolve the owning skill and exact `execution_domain` from the authoritative registry.
3. Apply safety, authority, modality, project, language, code-style, and owning-skill floors.
4. Select the lowest reliable static `model|effort` pair for the node's real work, never from the entry pair.
5. Validate the eligible weak-to-strong ladder and consult the exact calibrated profile, reusing its frozen `selected_pair` only when it remains eligible.
6. Validate the selected pair and explicit fallbacks, dependencies, inputs, output, and proof requirement before any side effect.

If a refreshed local cache temporarily omits a model that the current UI/runtime has already executed successfully, preserve the last validated capability snapshot and require a new runtime receipt. Do not silently rewrite the plan from one incomplete cache view.

## Model Roles

| Node condition | Preferred model | Typical effort |
|---|---|---|
| Missing context, open-ended synthesis, ambiguous architecture, or difficult cross-system judgment | `gpt-5.6-sol` | high, xhigh, max; ultra only when automatic delegation is both useful and authorized |
| Grounded, source-rich integration, repository search, realistic testing, or evidence-heavy review | `gpt-5.6-terra` | medium, high, xhigh |
| Direct bounded non-code work, concise writing, Mini Verify judgment, result delivery, or records | `gpt-5.6-luna` | low or medium |
| Text-only work in an active registry-owned code domain, repair, refactor, or authored probe | `gpt-5.3-codex-spark` plus `code-skill` | low, medium, high, or xhigh |

Use Spark first for every eligible implementation or authored probe in an active registry-owned code domain.

Do not assign Spark to image reading. Do not assign Luna merely because the requested wording is short when surrounding behavior is unclear. Do not assign Sol merely because a task is large when Terra has complete grounded sources.

## Effort Rubric

| Effort | Use when |
|---|---|
| low | One obvious bounded decision, edit, or check |
| medium | Clear multi-step work with ordinary judgment |
| high | Multi-file, integration, or evidence-heavy work |
| xhigh | Difficult debugging or several coupled systems |
| max | Hard single-agent reasoning with costly mistakes |
| ultra | Sol/Terra only, when authorized automatic delegation materially helps multiple substantial branches |

Never assign unsupported effort. Normalize `middle` to `medium`. If a requested effort is unsupported, use the nearest lower supported effort and show the normalization.

## Visible Fallbacks

- Spark unavailable, rejected, over context, image-dependent, or unavailable on the execution surface: use Luna for bounded work or Terra when context, image, search, or verification caused the mismatch.
- Sol unavailable: use Terra at the closest supported effort.
- Terra unavailable: use Sol for evidence-heavy judgment, or Luna only if remaining work is truly bounded.
- Luna unavailable: use Terra at low or medium.

Every fallback is a planned or observed event with `from`, `to`, reason, and effort. Never claim a fallback ran without execution metadata.

## Receipt-Backed Personal Learning

Use `scripts/model_routing_history.py recommend` with a controlled task profile and a weak-to-strong candidate ladder. Do not pass the entry model or effort into the recommendation function.

The learner performs a bounded calibration search for the selected complete `model|effort` pair per exact sanitized task profile. Effort changes always precede model changes in both directions. After adjacent verified pass/fail evidence establishes the bounds, or a verified pass proves the current hard floor, derive/reuse `selected_pair` with `trial=false`; do not repeatedly explore an unchanged calibrated profile.

The older shorthand "one cheaper/faster rung" means one lower eligible pair to measure; it is never a price or speed assumption and cannot bypass quality evidence.

- No prior success: use the static suggestion, except safe low-risk text-only `tiny_text`, `tiny_code`, or `command_generation` work starts at eligible Spark-low.
- Runtime failure of that Spark-low exception: use the static suggestion without recording a quality failure. Result nodes retry only exact planned `model|effort` fallbacks; Mini/Ending verdict failures do not model-retry.
- Verified Mini/Real pass while searching: trial exactly one lower rung, lowering effort on the same model first; after its eligible efforts are exhausted, try the next weaker eligible model.
- Receipt-matched Mini or Real correctness/quality failure: reopen calibration, keep a sticky failed boundary, and upgrade by effort first and model second. Exclude the failed and weaker rungs. If no stronger current candidate exists, return no selected pair and report the boundary exhausted.
- Eligible-ladder or hard-floor change: reopen calibration because the prior best may no longer be eligible or a newly inserted adjacent rung may need proof.
- Availability, timeout, protocol, telemetry, execution, or unverified/receipt-mismatch failure: treat as temporary diagnostic evidence only. It may use an explicit runtime fallback, but it does not change the learned quality best or quality boundaries.
- Record the main result-producer receipt after Mini and update that same attempt after Real; never learn the verifier model as the producer.
- Real Verify failure overrides an earlier Mini pass.
- High-risk, irreversible, or authority-sensitive work may record outcomes but must not auto-downgrade.

Use a correctness boundary and the weakest verified complete pair as the control selection anchor. Receipts are for like-for-like optimization evidence only and do not actively rank all candidates by median token or median process-time alone. Read `adaptive-routing.md` for the private schema and exact policy.

## Efficiency Guard

Model quality does not excuse wasteful context. Give a node an exact file/source allowlist, exclude caches and backups by default, and request a compact output contract. A broad raw dump can consume more time and tokens than the model choice saves.

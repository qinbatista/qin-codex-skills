# Per-Node Model And Effort Selection

Task Analyze runs on the model and effort currently selected at task entry. That pair may be any supported combination and stops being result-bearing authority when the visible route is shown.

## Selection Order

A routing rung is the complete `model_name|effort` pair. This is a weak-to-strong quality ladder, not a price ladder: never assume cross-model means cheaper. To downgrade, move exactly one eligible rung. Lower effort on the same model first; only after that model reaches its minimum eligible effort, move to the next weaker model at that model's highest eligible effort. Upgrade in the exact reverse direction after an Ending Real correctness/quality failure. Floors always win.

1. During bounded read-only preflight, call `scripts/resolve_entry_model.py` to preserve the current entry pair exactly; use `unverified` only when exact resolution fails. The entry pair is route metadata, never a learning feature.
2. Resolve the owning skill and exact `execution_domain` from the authoritative registry.
3. Apply safety, authority, modality, project, language, code-style, and owning-skill floors.
4. Select the lowest reliable static `model|effort` pair for the node's real work, never from the entry pair.
5. Validate the eligible weak-to-strong ladder and consult the exact calibrated profile, reusing its frozen `selected_pair` only when it remains eligible.
6. Validate the selected pair and explicit fallbacks, dependencies, inputs, output, and proof requirement before any side effect.

Every non-tiny model profile retains the exact complete GPT-5.6 Luna/Terra/Sol candidate ladder in its internal routing proof, even when the task is easy; selected pairs, fallbacks, and hard floors do not erase the recorded alternatives. A tiny eligible profile carries exactly Spark-low followed by that full normal fallback ladder.

Resolve a stable profile preset from the requested artifact before model selection. Inspected source language is not the execution domain: a read-only repository answer stays grounded/general even when its evidence is Python, C#, or Unity C#. Code presets apply only to code creation, changes, execution, or code-path validation.

If a refreshed local cache temporarily omits a model that the current UI/runtime has already executed successfully, preserve the last validated capability snapshot and require a new runtime receipt. Do not silently rewrite the plan from one incomplete cache view.

## Model Roles

| Node condition | Preferred model | Typical effort |
|---|---|---|
| Missing context, open-ended synthesis, ambiguous architecture, or difficult cross-system judgment | `gpt-5.6-sol` | high, xhigh, max; ultra only when automatic delegation is both useful and authorized |
| Grounded, source-rich integration, repository search, realistic testing, or evidence-heavy review | `gpt-5.6-terra` | medium, high, xhigh |
| Direct bounded non-code work, concise writing, Ending Real judgment, result delivery, or records | `gpt-5.6-luna` | low or medium |
| Obvious bounded, low-risk, easy, low-ambiguity text-only tiny text/code/command work in an active registry-owned code domain | `gpt-5.3-codex-spark` plus `code-skill` | low only |

These roles are cold-start hints, never permanent task-category assignments: coding and writing can each be easy or complex. Every non-tiny model route uses the exact full normal ladder from Luna low through Luna efforts, Terra efforts, and Sol ultra, with no Spark. Downgrade is effort first then model and upgrade reverses it. Tiny routes use Spark-low only plus the full normal fallback ladder; Spark-medium/high/xhigh are capability values, not adaptive-routing rungs.

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

- Spark-low unavailable, rejected, over context, image-dependent, or unavailable on the execution surface: use the learner-selected normal-ladder fallback; never raise Spark effort.
- Sol unavailable: use Terra at the closest supported effort.
- Terra unavailable: use Sol for evidence-heavy judgment, or Luna only if remaining work is truly bounded.
- Luna unavailable: use Terra at low or medium.

Every fallback is a planned or observed event with `from`, `to`, reason, and effort. Never claim a fallback ran without execution metadata.

## Receipt-Backed Personal Learning

Use `scripts/model_routing_history.py recommend` with one named profile preset, its required project/owner/domain values, and a sanitized summary. The preset derives the controlled condition and weak-to-strong candidate ladder internally. Do not pass the ladder, static pair, hard floor, entry model, or entry effort into the recommendation command.

The learner performs a bounded calibration search for the selected complete `model|effort` pair per exact sanitized task profile. Effort changes always precede model changes in both directions. Ending Real creates the quality verdict for the producer receipt/run, recomputes the recommendation, and freezes `best_pair` when eligible. Reuse a frozen exact-profile `selected_pair` with `trial=false` until verified failure, ladder/hard-floor/profile drift, policy change, or explicit reset.

Optional Obsidian `TaskModelExperience/` is a readable related-memory projection for Task Analyze and other skills after Ending Real. It may explain past switches, but it never replaces the private learner as exact pair authority. If Obsidian is unavailable, skip it without changing selection.

The older shorthand "one cheaper/faster rung" means one lower eligible pair to measure; it is never a price or speed assumption and cannot bypass quality evidence.

- No prior success: use the static suggestion, except safe low-risk text-only `tiny_text`, `tiny_code`, or `command_generation` work starts at eligible Spark-low.
- Runtime failure of that Spark-low exception: use the static suggestion without recording a quality failure. Result nodes retry only exact planned `model|effort` fallbacks; Ending verdict failures do not model-retry.
- Verified pass while searching: trial exactly one lower rung, lowering effort on the same model first; after its eligible efforts are exhausted, try the next weaker eligible model.
- Receipt-matched Ending Real correctness/quality failure: reopen calibration, keep a sticky failed boundary, and upgrade by effort first and model second. Exclude the failed and weaker rungs. If no stronger current candidate exists, return no selected pair and report the boundary exhausted.
- Eligible-ladder or hard-floor change: reopen calibration because the prior best may no longer be eligible or a newly inserted adjacent rung may need proof.
- Availability, timeout, protocol, telemetry, execution, or unverified/receipt-mismatch failure: treat as temporary diagnostic evidence only. It may use an explicit runtime fallback, but it does not change the learned quality best or quality boundaries.
- Record the main result-producer receipt and quality verdict only after Real; never learn the verifier model as the producer.
- High-risk, irreversible, or authority-sensitive work may record outcomes but must not auto-downgrade.

Correctness/quality is the eligibility gate. Cost-rank only Real-passing pairs that share the same exact `workload_prompt_sha256` cohort and have complete tokens and time for every compared pair. Within that cohort choose the lowest median total tokens, then median process time, then the weaker ladder rung. Cross-workload, missing-hash, incomplete, or single-pair evidence falls back to the verified quality boundary and cannot support a savings claim.

## Efficiency Guard

Model quality does not excuse wasteful context. Give a node an exact file/source allowlist, exclude caches and backups by default, and request a compact output contract. A broad raw dump can consume more time and tokens than the model choice saves.

For ordinary inline work, the current entry model performs the bounded task directly and presents the result without a foreground child or verifier. After different-pair delegation is admitted, the entry stops duplicating the child's source audit: one grounded producer reads the complete bounded allowlist. Split only genuinely disjoint routed source scopes, mark every collaboration child `LOCKED_ROUTE_NODE`, and choose collaboration or dispatcher once per branch. Use a 180-second easy or 600-second complex first-result deadline; Ending cost never blocks the first result.

This delegated path applies only after end-to-end performance admission. Ordinary work stays inline on the current model regardless of apparent complexity. Child quality and child-only cost cannot override the strategy gate: the complete Global path must repeatedly beat Direct in both total tokens and time for the exact entry/configuration/workload cohort.

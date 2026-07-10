# Per-Node Model And Effort Selection

Task Analyze runs on the model and effort currently selected at task entry. That pair may be any supported combination and stops being result-bearing authority when the visible route is shown.

## Selection Order

1. During bounded read-only preflight, call `scripts/resolve_entry_model.py` to preserve the current entry pair exactly; use `unverified` only when exact resolution fails.
2. Confirm the owning skill is installed.
3. Apply safety, authority, modality, project, language, and owning-skill floors.
4. Choose the static model by the node's real work, never by the entry pair.
5. Consult the matching private adaptive-routing profile and accept only a recommendation at or above every static floor.
6. Choose the lowest supported effort that can reliably meet the stop condition.
7. Record dependencies, inputs, output, fallback, routing profile, and proof requirement.
8. Validate the full plan before any side effect.

If a refreshed local cache temporarily omits a model that the current UI/runtime has already executed successfully, preserve the last validated capability snapshot and require a new runtime receipt. Do not silently rewrite the plan from one incomplete cache view.

## Model Roles

| Node condition | Preferred model | Typical effort |
|---|---|---|
| Missing context, open-ended synthesis, ambiguous architecture, or difficult cross-system judgment | `gpt-5.6-sol` | high, xhigh, max; ultra only when automatic delegation is both useful and authorized |
| Grounded, source-rich integration, repository search, realistic testing, or evidence-heavy review | `gpt-5.6-terra` | medium, high, xhigh |
| Direct bounded non-code work, concise writing, Mini Verify judgment, result delivery, or records | `gpt-5.6-luna` | low or medium |
| Text-only Python/C# implementation, repair, refactor, or authored Python/C# probe | `gpt-5.3-codex-spark` plus `code-skill` | low, medium, high, or xhigh |

Use Spark first for every eligible Python/C# implementation or authored probe.

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

Use `scripts/model_routing_history.py recommend` with a controlled task profile and a cheapest-to-strongest candidate ladder. Do not pass the entry model or effort into the recommendation function.

- No prior success: use the static suggestion, except safe low-risk text-only `tiny_text`, `tiny_code`, or `command_generation` work starts at eligible Spark-low.
- Runtime failure of that Spark-low exception: use the static suggestion without recording a quality failure. Result nodes retry only exact planned `model|effort` fallbacks; Mini/Ending verdict failures do not model-retry.
- Verified Mini/Real pass: trial exactly one cheaper/faster rung: one lower effort on the same model; after its eligible efforts are exhausted, try the next weaker eligible model.
- Mini or Real correctness/quality failure: sticky failed boundary; use the nearest eligible rung above it and exclude the failed and weaker rungs. If no stronger current candidate exists, return no selected pair and report the boundary exhausted.
- Availability, timeout, protocol, telemetry, execution, or receipt mismatch: do not count as quality evidence.
- Record the main result-producer receipt after Mini and update that same attempt after Real; never learn the verifier model as the producer.
- Real Verify failure overrides an earlier Mini pass.
- High-risk, irreversible, or authority-sensitive work may record outcomes but must not auto-downgrade.

Rank eligible verified choices by correctness first, then median total tokens, then median process time. Tokens are a usage proxy, not a currency claim. Read `adaptive-routing.md` for the private schema and exact policy.

## Efficiency Guard

Model quality does not excuse wasteful context. Give a node an exact file/source allowlist, exclude caches and backups by default, and request a compact output contract. A broad raw dump can consume more time and tokens than the model choice saves.

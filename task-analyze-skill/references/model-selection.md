# Spark-First Model Selection

The shared source of truth is `assets/model-capability-ladder.json`. The code reads it directly; this page is the human summary.

| Rank | Model | Best cold-start use | Codex efforts |
|---:|---|---|---|
| 1 | `gpt-5.6-luna` | Simple questions, summaries, routine spreadsheet/document transforms, small well-specified code edits, high-volume work | low, medium, high, xhigh, max |
| 2 | `gpt-5.6-terra` | Everyday coding, grounded repository work, debugging, moderate multi-file edits, structured analysis and spreadsheets | low, medium, high, xhigh, max, ultra |
| 3 | `gpt-5.6-sol` | Ambiguous architecture, hard debugging/review, complex integration, high-risk or long-horizon professional work | low, medium, high, xhigh, max, ultra |

Rank is approximate capability order, weakest to strongest, not a claim that every higher pair is cheaper or faster. OpenAI positions Luna for efficient high-volume work, Terra for intelligence/cost balance, and Sol as the frontier model for complex professional reasoning and coding.

## Effort Order

`low -> medium -> high -> xhigh -> max -> ultra`

- `low`: bounded and latency-sensitive.
- `medium`: ordinary balanced default.
- `high` / `xhigh`: use when representative tasks show a quality gain.
- `max`: hardest quality-first work.
- `ultra`: Codex automatic delegation for several substantial independent branches; only Terra and Sol expose it locally.

Official GPT-5.6 API guidance also lists `none`; the current local Codex catalog does not expose it, so it is not an adaptive rung. Conversely, `ultra` is a Codex execution mode rather than an ordinary API reasoning-effort name.

## Selection Rules

Use the task preset only as a cold-start hint. Then read the matching Obsidian `Projects/<project-key>/ModelExperience` boundary keyed by project/task/module/file/symbol/code context. A receipt-backed Ending Real pass moves one rung lower; a quality failure moves one rung higher; repeated passes may reach and freeze Luna-low. Operational failures do not change quality rank, and Ending Real alone writes the verdict.

Promotion and demotion stay inside the exact 5.6 ladder. Separately, eligible text/code result producers try Spark-low for easy work or Spark-high for complex work. Zero-result operational failure uses the contextual 5.6 pair; Ending quality/correctness failure is recorded before a new 5.6 repair lifecycle. Exact read-only stays inline, and old local `model_experience.json` stays legacy read-only. The ordinary producer uses `obsidian_adaptive_model_runner.py`; multi-node strategy remains separately performance-admitted.

The documentation basis checked on 2026-07-13 is the official OpenAI model catalog and GPT-5.6 guidance plus the local Codex `models_cache.json` for actually exposed efforts.

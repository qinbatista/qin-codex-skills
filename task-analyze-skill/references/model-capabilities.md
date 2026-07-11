# Cached Model Capabilities

Use this local snapshot during `task-analyze-skill`. Do not query the runtime model catalog on every task. Refresh only when the user asks for current capabilities, this file is missing, the runtime rejects a model/effort, or the model list changes.

If a refreshed cache omits one of these models while the current Codex UI/runtime still executes it, preserve this last validated snapshot, report the cache as incomplete, and require a runtime receipt before using or changing that route.

- Source: `~/.codex/models_cache.json`
- Codex client version: `0.144.0`

| Display name | Model ID | Inputs | Context | API | Default effort | Supported efforts | Speed tiers |
|---|---|---|---:|---|---|---|---|
| GPT-5.3-Codex-Spark | `gpt-5.3-codex-spark` | text | 128,000 | no | `high` | low, medium, high, xhigh | default |
| GPT-5.6-Luna | `gpt-5.6-luna` | text, image | 372,000 | yes | `medium` | low, medium, high, xhigh, max | fast |
| GPT-5.6-Terra | `gpt-5.6-terra` | text, image | 372,000 | yes | `medium` | low, medium, high, xhigh, max, ultra | fast |
| GPT-5.6-Sol | `gpt-5.6-sol` | text, image | 372,000 | yes | `medium` | low, medium, high, xhigh, max, ultra | fast |

## Effort Compatibility

- `gpt-5.3-codex-spark`: low, medium, high, xhigh.
- `gpt-5.6-luna`: low, medium, high, xhigh, max.
- `gpt-5.6-terra`: low, medium, high, xhigh, max, ultra.
- `gpt-5.6-sol`: low, medium, high, xhigh, max, ultra.
- Sol, Terra, and Luna accept image input. Spark is text-only.
- Spark is unavailable through API-only execution surfaces.
- Capability support does not equal routing eligibility: adaptive routes may use Spark-low only, and only for an eligible tiny profile; Spark medium/high/xhigh are never adaptive fallbacks.
- If an effort is unsupported, use the highest supported effort below it and show the normalization.

## Refresh

```bash
python3 scripts/sync_model_capabilities.py
python3 scripts/sync_model_capabilities.py --check
```

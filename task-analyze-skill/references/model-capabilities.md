# Available model capabilities

This local catalog snapshot is used only for skill-independent adaptive work. The user's selected model and effort govern skill work and memory summaries, even when this snapshot is older than their selection.

| Model | Supported efforts |
|---|---|
| `gpt-6-astra` | low, medium, high, xhigh, max, ultra |
| `gpt-5.6-sol` | low, medium, high, xhigh, max, ultra |
| `gpt-5.6-terra` | low, medium, high, xhigh, max, ultra |
| `gpt-5.6-luna` | low, medium, high, xhigh, max |
| `gpt-5.5` | low, medium, high, xhigh |
| `gpt-5.4-mini` | low, medium, high, xhigh |
| `gpt-5.3-codex-spark` | low, medium, high, xhigh |

Catalog priority provides a cold-start quality order; measured same-project outcomes may refine independent-task choices. Operational failures do not grade model quality. Ending is memory-only with the selected pair and no automatic fallback.

Use `sync_model_capabilities.py --update` for an explicitly requested catalog refresh. Ordinary task execution does not refresh this file.

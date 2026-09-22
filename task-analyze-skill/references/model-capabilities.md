# Available model capabilities

Catalog digest: `049bef806afc754f0b57d861fbbca6116bf3bc9deeca2ec315de0fcde345929c`

This local catalog snapshot is used only for skill-independent adaptive work. The user's selected model and effort govern skill work and memory summaries, even when this snapshot is older than their selection.

| Model | Supported efforts |
|---|---|
| `gpt-6-astra` | low, medium, high, xhigh, max, ultra |
| `gpt-6-sol` | low, medium, high, xhigh, max, ultra |
| `gpt-6-luna` | low, medium, high, xhigh, max |

Catalog priority provides a cold-start quality order; measured same-project outcomes may refine independent-task choices. Operational failures do not grade model quality. Ending is memory-only with the selected pair and no automatic fallback.

Use `sync_model_capabilities.py --update` for an explicitly requested catalog refresh. Ordinary task execution does not refresh this file.

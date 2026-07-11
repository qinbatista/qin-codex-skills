# Optional Related Memory

## Purpose

Use a quick memory lookup to improve one task with related past requirements, verified failures, retry lessons, project facts, and model-switch experience. Memory is advisory context, never a reason to delay or replace source inspection.

## Task-Start Search

Run `scripts/obsidian_memory_bridge.py search --query <generalized task summary>` during bounded read-only Task Analyze preflight when a vault is available. The bridge searches `TaskModelExperience/` and structured skill/project/taste/knowledge folders before DailyLog and generic wiki pages, returns only a bounded digest, and never returns raw transcripts or secrets.

- Use only matches that materially affect the current task.
- Prefer exact project, skill, failure, requirement, and verification nouns.
- Pass the concise digest only to nodes that need it.
- Recheck live source when memory may be stale.
- If the bridge returns `unavailable` or `no_matches`, continue normally without warning, setup work, or a blocked route.

The private `local/adaptive-routing/model_experience.json` ledger remains the only machine authority for exact model/effort selection. Obsidian `TaskModelExperience/` is a sanitized human-readable reference for Task Analyze and other skills.

## Ending Update

After the Mini-verified result is shown, Ending Task may update only memory related to the completed work. Write model-switch experience only after Real Verify has produced a durable verdict. Use `scripts/obsidian_memory_bridge.py record-model` with controlled profile fields, producer pair, Mini/Real status, boundary state, switch reason, and comparable metrics when available.

Never store raw prompts, results, absolute paths, thread/session IDs, receipt bodies, credentials, secrets, or unrelated task history. Missing Obsidian remains a successful no-op.

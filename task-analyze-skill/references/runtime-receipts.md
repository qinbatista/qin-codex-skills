# Runtime receipts

Receipts record requested, resolved and effective model/effort, completion status, token totals and timing. Match the exact runtime pair; a configured selection or task assignment is not a completed run. Never fabricate receipt evidence for inline tool work.

A process success alone does not prove its output correct. The active task owns relevant verification and final aggregation, including a failed aggregate verdict. Simple value-only edits can explicitly skip verification.

Skill-governed receipts retain the user's selected pair with no automatic fallback. Independent-task operational fallback must retain failed attempts and aggregate token/time costs. Only in-task behavior evidence may inform correctness learning; memory Ending cannot.

Use `model_identity_disclosure.py` to disclose the task score, model and route, and each delegated stage. Surface its message in the conversation; JSON fields hidden in tool output are insufficient. It distinguishes runtime receipts, verified entry identity, task assignment and unavailable identity. Keep routing artifacts private under project `Cache/tmp-*`, and never place raw prompts or results into shared model capability metadata.

Default child execution prefers an explicit `CODEX_RUNTIME_EXECUTABLE` binding or the verified active Codex host executable before PATH. Explicit `--codex-bin` paths remain authoritative. A client-version rejection is an operational compatibility failure: use a compatible runtime and retry the same selected model; do not grade or downgrade the model. Receipts record the executable and its source.

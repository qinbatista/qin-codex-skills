---
name: project-memory-skill
description: "Recall relevant project memory and record concise durable outcomes or preferences with the user's selected model. Skip unavailable memory."
---

# Project Memory

Memory reduces repeated explanations. Preserve current code ownership and structure, UI preferences, document organization, important decisions, and unresolved limitations. The user's selected model and reasoning effort read and summarize it.

## Recall before work

Resolve the actual project first. Use its explicit vault or registered configuration; never guess from a same-name folder. Read the matching project summary, relevant module or preference, and at most five matching events. Read relevant shared preferences only from their explicit shared owner, never by searching unrelated projects.

For a root-first vault, use `AI Memory/ai_memory.py recall --project NAME --module MODULE --query TEXT`. Existing local results use `scripts/project_change_memory.py search --project-root ROOT --module MODULE --max-results 5`. Missing vault, project, or memory is a normal skip. Do not create a fallback memory hierarchy just to satisfy a skill.

Current user intent and source evidence take precedence over memory. Effective records guide work; superseded records are history. Registered aliases may represent one project, while unregistered clones remain separate.

## Ending: memory only

After work and relevant verification finish in the active task, record only information likely to help a future task. For the user-authorized Ending lifecycle, create one separate projectless task using the user's selected model and effort. That task reads related memory, summarizes the completed outcome, writes through the supported writer and reads it back. Show its actual task link and pending/completed/skipped status. A launch packet or inline write is not proof that this separate task ran. Leave the Ending conversation as an ordinary unpinned task in Codex's session list. Visibility means providing its link and reading its status; do not pin, move, reorder, or open it automatically. If the app omits an acknowledged task from recent tasks, read it by its existing ID and report the link without changing its sidebar placement or creating a duplicate. Ending never verifies the project, runs builds, repairs, benchmarks, downgrades its model or creates further tasks.

Keep one concise current owner for each fact. Summarize what changed, why, affected structure or preference, and actual verification status. Preserve meaningful limitations; do not turn untested behavior into a verified claim. Skip when nothing durable changed or memory is unavailable.

Use the vault's supported writer and amendment/supersession operations. Keep history in its event store and use a compact current summary for ordinary recall. In an existing local store, `project_change_memory.py record` retains project/file scope and reconciles same-ID projections. `scripts/ending_memory.py` accepts a completed outcome from the selected model and performs only this memory write. `scripts/ending_memory_launch.py` prepares the visible task handoff and validates acknowledgement; the parent uses the app task API and reports unavailable creation as pending. A user request to use this Ending lifecycle authorizes its memory task; do not infer authorization from unrelated work.

## Isolation and privacy

- Require a project for ordinary recall and writes. Cross-project searches are explicit audits, never task context.
- Keep project-specific decisions in that project. Only explicitly general preferences belong in shared memory.
- Save concise facts and project-relative files, not raw prompts, transcripts, reasoning, credentials, absolute host paths, or other projects' content.
- Do not hand-edit event stores. Read back the saved result; failed projections remain pending rather than being reported as synchronized.
- Preserve unrelated records and useful history. Put probes in an explicit isolated store under `Cache/tmp-*`; never test against production memory.

Adaptive routing history is separate from user/project memory. Its outcomes may adjust only skill-independent tasks; it never overrides the user's selected model for skill-governed work or memory.

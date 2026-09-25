---
name: project-memory-skill
description: "Ensure a durable Obsidian vault, recall exact-project memory, and record concise outcomes with the user's selected model."
---

# Project Memory

Memory reduces repeated explanations. Preserve current code ownership and structure, UI preferences, document organization, important decisions, and unresolved limitations. The user's selected model and reasoning effort read and summarize it.

## Recall before work

Resolve the actual project first. Run `scripts/obsidian_vault_setup.py --project-root PROJECT_ROOT` to find the configured memory vault. If none exists, it connects to [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki), generates a private vault outside Codex and the project, and verifies it. Use `--vault PATH` for a chosen durable location or `--source PATH` for an offline copy of the generator. Never place the vault in `CODEX_HOME` or project `Cache`. Report the exact returned vault location and tell the user to back up the whole vault regularly because it holds all Codex and project memory. If setup fails, report the reason and leave writes pending without local fallback.

On a replacement computer, restore or sync the existing whole vault before memory setup or new writes. A registered or configured vault that is unavailable or still syncing is pending; wait for that vault instead of generating an empty replacement. The public generator provides structure for a first vault, not a backup of private memories. Verify the restored `AI Memory` and `Projects` contents before claiming recovery.

Read the matching project summary, relevant module or preference, and at most five matching events. Read relevant shared preferences only from their explicit shared owner, never by searching unrelated projects.

For a root-first vault, use `AI Memory/ai_memory.py recall --project NAME --module MODULE --query TEXT`. Legacy Codex-local memory is read-only migration input, never an ongoing memory owner. A missing matching project or note is a normal read skip after vault setup; never substitute another project's memory.

Current user intent and source evidence take precedence over memory. Effective records guide work; superseded records are history. Registered aliases may represent one project, while unregistered clones remain separate.

## Ending: memory only

After the main task and real verification finish, record only information likely to help a future task. For the user-authorized Ending lifecycle, create one separate projectless task using the user's selected model and effort. It writes directly to the configured Obsidian vault and reads back the saved result there. Show its task link and status. Leave it as an ordinary unpinned task in Codex's recent tasks; do not pin, move, reorder, open, archive, or duplicate it automatically. Its pending or failed state does not change the completed main task or another active task. Ending never tests, builds, repairs, benchmarks, publishes, or creates further tasks.

Keep one concise current owner for each fact. Summarize what changed, why, affected structure or preference, and actual verification status. Preserve meaningful limitations; do not turn untested behavior into a verified claim. Skip when nothing durable changed. Put changing project facts in `Projects/<Project>/Knowledge.md` and shared facts under their explicit vault owner. When a durable rule changes, review relevant project `AGENTS.md` and Skills and update stable operating instructions there; do not add a changing memory log to either.

Use the vault's supported writer and amendment/supersession operations. Keep history in `AI Memory/events.jsonl` and one current entry per module in `Projects/<Project>/Knowledge.md` for ordinary recall. `scripts/ending_memory.py` accepts a completed outcome from the selected model, registers a new project through the vault runtime, and writes only to Obsidian; it attempts vault setup if needed. `scripts/ending_memory_launch.py` prepares the visible task handoff and validates acknowledgement; the parent uses the app task API and reports unavailable creation as pending. A user request to use this Ending lifecycle authorizes its memory task; do not infer authorization from unrelated work. If setup or the vault is unavailable, stop the memory write and report pending; never queue it under Codex.

## Isolation and privacy

- Require a project for ordinary recall and writes. Cross-project searches are explicit audits, never task context.
- Keep project-specific decisions in that project. Only explicitly general preferences belong in shared memory.
- Save concise facts and project-relative files, not raw prompts, transcripts, reasoning, credentials, absolute host paths, or other projects' content.
- Do not hand-edit event stores. Read back the saved result from Obsidian before claiming it is saved.
- Preserve unrelated records and useful history. Put probes in an explicit isolated store under `Cache/temp-*`; never test against production memory.
- Never put durable memory, dated project outcomes, pending memory queues, routing history, coverage records, or memory location pointers in `CODEX_HOME`, `~/.codex`, project `Cache`, or project `AGENTS.md`/Skill files. Those project files contain stable rules and workflow instructions only.

Adaptive routing history is separate from user/project memory but is also stored only in the configured Obsidian vault. Its outcomes may adjust only skill-independent tasks; it never overrides the user's selected model for skill-governed work or memory.

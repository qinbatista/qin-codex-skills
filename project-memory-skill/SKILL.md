---
name: project-memory-skill
description: "Maintain centralized Obsidian project knowledge, recall exact project/module/file/symbol context, and consolidate durable outcomes and relationships."
---

# Project Memory

Memory reduces repeated explanations. Preserve project architecture, ownership, module responsibilities, relevant method contracts, decisions, preferences, and unresolved limitations in one project knowledge store. Read [project knowledge](references/project-knowledge.md) for scoped recall, addressable entries, and consolidation.

## Recall before work

Resolve the actual project first. Run `scripts/obsidian_vault_setup.py --project-root PROJECT_ROOT` to find the configured memory vault. If none exists, it connects to [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki), generates a private vault outside Codex and the project, and verifies it. Use `--vault PATH` for a chosen durable location or `--source PATH` for an offline copy of the generator. Never place the vault in `CODEX_HOME` or project `Cache`. Report the exact returned vault location and tell the user to back up the whole vault regularly because it holds all Codex and project memory. If setup fails, report the reason and leave writes pending without local fallback.

On a replacement computer, restore or sync the existing whole vault before memory setup or new writes. A registered or configured vault that is unavailable or still syncing is pending; wait for that vault instead of generating an empty replacement. The public generator provides structure for a first vault, not a backup of private memories. Verify the restored `AI Memory` and `Projects` contents before claiming recovery.

Use `scripts/project_knowledge.py recall --project-root ROOT --vault VAULT` with the narrowest relevant module, project-relative file, and symbol filters. Method recall requires a module, exactly one file, and one or more symbols; filter types combine with AND. Start from current entries and their relevant relationships; expand to project architecture only when ownership or dependencies require it. Historical events explain provenance and are not the default task context. Read shared preferences only from their explicit shared owner.

Current knowledge lives in `Projects/<owner>/Memory.json`, with a readable `Knowledge.md` view. Existing `AI Memory/events.jsonl` preserves history. Do not create a memory file for every task, module, or method, or prepopulate entries for untouched code. Legacy Codex-local memory is read-only migration input, never an ongoing memory owner. A missing index, matching project, or entry is a normal read skip after vault setup; an owner conflict also skips recall. Never fall back to an unscoped history search or another project's memory.

Current user intent and source evidence take precedence over memory. Entries are current or explicitly retired; superseded versions remain history. Recall excludes stale entries and returns methods with absent source hashes separately as unverified pointers, never eligible current context. Current status or a matching source hash does not prove runtime behavior. Refresh consequential claims against current source or actual output. Registered aliases may represent one project, while unregistered clones remain separate.

## Ending: memory only

After the main task and real verification finish, record only information likely to help a future task. For the user-authorized Ending lifecycle, create one separate projectless task with the app's defaults. It writes directly to the configured Obsidian vault and reads back the saved result there. Show its task link and status. Leave it as an ordinary unpinned task in Codex's recent tasks; do not pin, move, reorder, open, archive, or duplicate it automatically. Its pending or failed state does not change the completed main task or another active task. Ending never tests, builds, repairs, benchmarks, publishes, or creates further tasks.

Consolidate touched entries on every Ending: read their prior current state, incorporate established changes, and save complete current truth with relevant relationships. A method update does not replace its module summary. Retire exact old scopes for a rename or deletion, and preserve unrelated facts. Record the resulting contract and actual verification status without duplicating summaries. Source evidence belongs to the originating task; Ending must not hash current code and relabel old claims as verified. Project synthesis becomes due after 20 distinct writes or 30 days. Check due status and synthesize on the first Ending run after that threshold is reached; do not create an automation or another task chain. Skip when neither durable updates nor useful consolidation is needed.

Use the supported memory writers, never hand-edit event or index stores. `scripts/ending_memory.py` accepts a completed outcome and updates central project knowledge with event provenance; it registers a new project through the vault runtime and attempts vault setup if needed. `scripts/ending_memory_launch.py` prepares the visible task handoff and validates acknowledgement; the parent uses the app task API and reports unavailable creation as pending. A user request to use this Ending lifecycle authorizes its memory task; do not infer authorization from unrelated work. Read back the event and current knowledge before reporting success. If setup or the vault is unavailable, report pending without a local queue.

Shared facts stay under their explicit vault owner. An authorized durable operating-rule change belongs in the relevant `AGENTS.md` or Skill under the [authoring rules](../management-skill/SKILL.md#authoring-rules). Ordinary outcomes and memory consolidation do not trigger instruction edits; changing project facts stay in the vault. Ending records completed changes and does not maintain Skills.

## Isolation and privacy

- Require exact project identity for ordinary recall and writes. Cross-project comparisons or deliberately selected reference links are separate reference material, never authoritative facts about the active project. Do not search or merge unrelated projects by similar names.
- Keep project-specific decisions in that project. Only explicitly general preferences belong in shared memory.
- Save concise facts and project-relative files, not raw prompts, transcripts, reasoning, credentials, absolute host paths, or other projects' content.
- Do not hand-edit event stores. Read back the saved result from Obsidian before claiming it is saved.
- Preserve unrelated records and useful history. Put probes in an explicit isolated store under `Cache/temp-*`; never test against production memory.
- Never put durable memory, dated project outcomes, pending memory queues, coverage records, or memory location pointers in `CODEX_HOME`, `~/.codex`, project `Cache`, or project `AGENTS.md`/Skill files. Those project files contain stable rules and workflow instructions only.

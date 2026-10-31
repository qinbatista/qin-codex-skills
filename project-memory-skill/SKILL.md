---
name: project-memory-skill
description: "Maintain centralized Obsidian project knowledge, recall exact project/module/file/symbol context, and consolidate durable outcomes and relationships."
---

# Project Memory

Before support/probe writes, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Isolate them in the owning project Cache from the first write; durable memory keeps its configured Obsidian owner.

Memory reduces repeated explanations. Preserve project problems and user struggles/corrections, attempted solutions, last verified state and date, actual results and evidence, unresolved items and next steps, alongside architecture, ownership, contracts, decisions and preferences in one project knowledge store. Capture useful established outcomes at completion, failure or pause; retain the actual blocker, partial or failed result and next step without inventing proof. Use the existing reason, result, decisions, verification and risks fields; do not invent whole-project status from a passing check. Read [project knowledge](references/project-knowledge.md) for scoped recall, addressable entries, and consolidation.

## Recall before work

When the current task prohibits creating external directories, invoke `scripts/obsidian_vault_setup.py --project-root PROJECT_ROOT --existing-only`. This mode reuses an existing vault and returns `pending` with `vault_creation_disabled` if creation would be needed, without creating parent directories, cloning or running the generator. Skip unavailable recall without creating a fallback. An explicit `--vault` path alone does not lift this boundary.

Resolve the actual project first. Run `scripts/obsidian_vault_setup.py --project-root PROJECT_ROOT` to find the configured memory vault. If none exists, it connects to [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki), generates a private vault outside Codex and the project, and verifies it. Use `--vault PATH` for a chosen durable location or `--source PATH` for an offline copy of the generator. Never place the vault in `CODEX_HOME` or project `Cache`. Report the exact returned vault location and tell the user to back up the whole vault regularly because it holds all Codex and project memory. If setup fails, report the reason and leave writes pending without local fallback.

On a replacement computer, restore or sync the existing whole vault before memory setup or new writes. A registered or configured vault that is unavailable or still syncing is pending; wait for that vault instead of generating an empty replacement. The public generator provides structure for a first vault, not a backup of private memories. Verify the restored `AI Memory` and `Projects` contents before claiming recovery.

Use `scripts/project_knowledge.py recall --project-root ROOT --vault VAULT` with at least one relevant task module, project-relative file or meaningful query; method lookup also needs the exact symbol filters. An unfiltered call is a skip, while explicit `--include-project-context` without task selectors returns only project facts and navigation. Method recall requires a module, exactly one file, and one or more symbols; filter types combine with AND. Start from current entries and their relevant relationships; expand to project architecture only when ownership or dependencies require it. Historical events explain provenance and are not the default task context. Read shared preferences only from their explicit shared owner.

Current knowledge lives in `Projects/<owner>/Memory.json`, with a readable `Knowledge.md` view. Existing `AI Memory/events.jsonl` preserves history, including prior failed attempts and superseded solutions. Repeated issues use a stable issue ID with one revision per distinct outcome; identical replays add nothing. Issue resolution is explicit and separate from check status. Do not create a memory file for every task, module, or method, or prepopulate entries for untouched code. Legacy Codex-local memory is read-only migration input, never an ongoing memory owner. A missing index, matching project, or entry is a normal read skip after vault setup; an owner conflict also skips recall. Never fall back to an unscoped history search or another project's memory.

For an unknown module label, use `project_knowledge.py scopes --project-root ROOT --vault VAULT --query TASK_TERMS` (or `--file FILE`) to locate bounded identifiers without loading facts. Recall only the selected scope through the normal freshness gate; discovery pointers are not current evidence.

Use the index in this order: project → task-relevant memory → underlying logic. After scoped recall, `project_knowledge.py logic` with the same task selectors follows declared `applies-logic` relationships to a shared `logic.*` principle and related case pointers. Excluded stale/unverified scopes retain reviewed logic pointers, with their claims withheld; retired scopes supply no routes. If no task link exists, identify the principle from the request/current source and select it explicitly with `--principle-owner OWNER --principle logic.KEY`. Matching keywords alone do not establish matching logic. Read only selected exact-owner references, compare the common principle, applicability and concrete differences, and retain dates/proof limits. Cross-project implementations remain reference material, never facts about the active project. See [the logic contract](references/project-knowledge.md#project-task-and-underlying-logic).

Current user intent and source evidence take precedence over memory. Entries are current or explicitly retired; superseded versions remain history. Recall excludes stale entries and returns methods with absent source hashes separately as unverified pointers, never eligible current context. Current status or a matching source hash does not prove runtime behavior. Refresh consequential claims against current source or actual output. Registered aliases may represent one project, while unregistered clones remain separate.

Keep Codex's automatic memory injection and generation disabled when Obsidian is the memory owner; injected summaries can span unrelated projects. Ordinary recall never loads event history or prose as a fallback for a structured owner. Select historical evidence explicitly and keep it separate from current authority. When the user requests legacy cleanup, remove obsolete imports, duplicate owners and retired routing or coverage files after verifying the current handoff; update references and remove unused writers. Do not create replacement archives or compatibility copies. The canonical event store remains the single useful chronology.

Existing conversations can retain an earlier injected memory instruction after configuration changes. Check effective settings separately from their retained context and subsequent reads; an API acknowledgement or compaction does not prove removal. If the owning service has no supported context repair, report that boundary and prepare a minimal exact-project handoff for a clean conversation, preserving the original record. Creating that conversation requires explicit user authorization; a history-copying fork carries the same risk. Never edit Codex session/database files or substitute another service's unloaded-thread state for the owning app's state.

For a verified move or second-machine checkout, use the explicit `project_knowledge.py register-alias` repair described in [project knowledge](references/project-knowledge.md#registered-root-aliases). It requires the exact registered root, expected owner, stored project key, and current index SHA. Ordinary recall never registers an alias or adopts memory by project name.

## Inline guidance, memory and resource closure

Finish the current project’s guidance, scoped memory and Workflow resource cleanup in the originating chat. Do not create an automatic Ending conversation. Codex chats, sessions and databases belong to the user’s manual lifecycle; Cache cleanup never archives, deletes or purges them. Existing conversation helpers are explicit-user-request tools only, not automatic closeout steps.

Apply Management’s current-project index check before delivery. Reconcile established source ownership and concise rules, and refresh its bounded operational Cache index after cleanup. Consulted projects remain reference-only unless the user explicitly requests their update. Preserve first-bootstrap consent, unrelated edits and read-only boundaries.

Write useful established project facts only to the configured Obsidian vault, with source-bound verification and current-state readback. Consolidate touched scopes, preserving history and unrelated knowledge. Check due synthesis through the existing owner; unavailable memory stays pending and never blocks independent resource cleanup. Do not create a local pending queue, a memory file per task, or another chat to perform this work.

Release completed disposable resources through their actual owners in the active task. Retain only the requested deliverable, live debugging inputs or minimum current recovery state. Package/upload and testing outcomes follow Workflow’s immediate consumption and 72-hour idle-task policy; current operational Cache information is an explicit bounded index exception, not project knowledge or a history log.

### Ending conversation cleanup

Codex sessions are manual user operations. Never invoke `ending_conversation.py` or an app deletion/archive tool as automatic Cache or task closeout. Its legacy native deletion helper is available only when the user explicitly asks for that exact conversation operation; it never authorizes direct database/session-file purges.

## Isolation and privacy

- Require exact project identity for ordinary recall and writes. Cross-project comparisons or deliberately selected reference links are separate reference material, never authoritative facts about the active project. Do not search or merge unrelated projects by similar names.
- Keep project-specific decisions in that project. Only explicitly general preferences belong in shared memory.
- Save concise facts and project-relative files, not raw prompts, transcripts, reasoning, credentials, absolute host paths, or other projects' content.
- Do not hand-edit event stores. Read back the saved result from Obsidian before claiming it is saved.
- Preserve unrelated records and useful history. Put probes in an isolated project Cache task store under the [artifact policy](../workflow-skill/references/project-cache-artifact-policy.md); never test against production memory.
- Never put durable memory, dated project outcomes, pending memory queues, coverage records, or memory location pointers in `CODEX_HOME`, `~/.codex`, project `Cache`, or project `AGENTS.md`/Skill files. Those project files contain stable rules and workflow instructions; the sole operational exception is the bounded, ignored AI-index cache/current.json snapshot owned by Management and Workflow.

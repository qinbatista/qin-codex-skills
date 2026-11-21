---
name: project-memory-skill
description: "Maintain centralized Obsidian project knowledge, recall exact project/module/file/symbol context, and consolidate durable outcomes and relationships."
---

# Project Memory

Before writing support or probes, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Keep scratch in the owning project Cache from its first write and durable memory in Obsidian.

Record durable project architecture, ownership, contracts, decisions, preferences, problems, user corrections and attempted solutions in one store. At completion, failure or pause, capture the verified state and date, actual results and evidence, open issues and next steps. Use existing reason, result, decisions, verification and risks fields. Keep claims at the scope verified. Follow [project knowledge](references/project-knowledge.md) for recall, entries and consolidation.

Write and review all new or revised durable prose in English, including entries, synthesis and event summaries. Preserve exact evidence and event history.

## Recall before work

Resolve the actual project first. Run `scripts/obsidian_vault_setup.py --project-root PROJECT_ROOT` to find the configured vault or generate the first private vault from [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki) outside Codex and the project. Use `--vault PATH` for a chosen location or `--source PATH` for an offline generator. Report the verified vault path and remind the user to back up the whole vault containing Codex and project memory regularly.

When external creation is prohibited, add `--existing-only` even if `--vault` is specified. A missing vault then returns `pending` with `vault_creation_disabled` before parent creation, cloning or generation. On setup failure, report the reason, skip recall and leave writes pending. Use only the configured vault for storage.

On a replacement computer, restore or sync the whole existing vault and verify `AI Memory` and `Projects`. Keep an unavailable or syncing registered vault pending until it is accessible. The generator is for first-vault setup only.

Run `scripts/project_knowledge.py recall --project-root ROOT --vault VAULT` with a relevant module, project-relative file or meaningful query. For method recall, give a module, exactly one file and one or more exact symbols. Filter types combine with AND. Unfiltered calls skip. Explicit `--include-project-context` without selectors returns only project facts and navigation. Start with current entries and relevant relationships, expanding to architecture only for ownership or dependencies. Select shared preferences from their explicit owner.

Use `Projects/<owner>/Memory.json` for current knowledge and `Knowledge.md` for its readable view. Keep failures and superseded solutions in the existing `AI Memory/events.jsonl` history. Give repeated issues a stable ID and one revision per distinct outcome. Record issue resolution explicitly, apart from check status. Add only established facts to the existing store. Treat legacy Codex-local memory as read-only migration input. Skip recall for a missing index, project or matching entry, or an owner conflict.

For an unknown module, locate identifiers with `project_knowledge.py scopes --project-root ROOT --vault VAULT --query TASK_TERMS` or `--file FILE`. Use the normal recall freshness check for the selected scope before relying on its facts.

Follow project → task memory → underlying logic under [the logic contract](references/project-knowledge.md#project-task-and-underlying-logic). After recall, run `project_knowledge.py logic` with the same selectors to follow declared `applies-logic` links to `logic.*` principles and case pointers. Stale or unverified scopes expose only reviewed logic pointers. Retired scopes supply no routes. Without a task link, choose a principle from the request or source with `--principle-owner OWNER --principle logic.KEY`. Read only selected references and compare applicability, differences, dates and evidence limits. Treat cross-project cases as references.

Current user intent and source take precedence. Recall excludes stale and retired facts and returns methods without source hashes only as unverified pointers. Refresh consequential claims from source or actual output. A current entry or matching hash establishes source context only. Registered aliases may link roots for the same project. Unregistered clones remain separate.

Keep Codex automatic memory injection and generation disabled when Obsidian owns memory. Ordinary recall uses scoped current records only. Select historical evidence explicitly, apart from current authority. For requested legacy cleanup, verify handoff, update references and remove obsolete imports, duplicate owners, retired routing or coverage files and unused writers. Keep the existing event store as the sole archive and avoid compatibility copies.

Existing chats can retain injected instructions after settings change. Check settings, retained context and subsequent reads in the owning app. API acknowledgements, compaction and history-copying forks can leave stale context in place. If supported repair is unavailable, report the limit and prepare a minimal exact-project handoff while preserving the original record. Creating a clean chat requires explicit authorization. Never edit Codex session or database files.

For a verified move or second-machine checkout, use [`project_knowledge.py register-alias`](references/project-knowledge.md#registered-root-aliases) with the exact registered root, expected owner, stored project key and current index SHA. Keep ordinary recall scoped to the registered identity.

## Inline guidance, memory and resource closure

Finish current-project guidance, memory and resources quietly in the originating chat. Handle routine authorized housekeeping directly. Leave any action needing authorization, elevation or an unavailable API pending and report the reason. Keep closeout in this chat without creating Ending tasks, automations or workers. Codex chats, sessions and databases remain user-managed, including when verifying a repair.

Before delivery and at closeout, run Management's current-project inspection with changed paths. For every project change, update and read back relevant index routes, docs or metadata even when memory has no new facts. Reconcile root guidance as needed and refresh the bounded Cache inventory after cleanup. Honor first-bootstrap consent, unrelated edits, read-only limits and reference-only scope. Report specific pending work.

Before the final response, use `scripts/ending_memory.py` with the verified vault. For eligible facts, record module, summary, reason, result, files, actual verification and `source_hashes` from `ending_memory.snapshot_sources` at verification time. Stage the outcome only in the task Cache. Check returned status and read back the same-project event and current memory. With no eligible facts, use `{"durable": false}` to check synthesis and record a no-op as a skip. If the existing vault is unavailable, keep the write pending.

Consolidate touched scopes while preserving history and unrelated knowledge. Check due and [AI-index triggered synthesis](references/project-knowledge.md#ai-index-triggered-synthesis). Report the exact reason for pending writes, readbacks or synthesis. Continue independent cleanup.

Run [Workflow's leftover check](../workflow-skill/references/ending-resource-audit.md#check-and-reclaim-task-leftovers) at closeout. Apply [the cleanup plan](../workflow-skill/references/project-cache-artifact-policy.md#plan-before-producing-files) after each verified and reported result. Hand off deliverables to their owners and release disposables. Retain exact necessary active/recovery inputs or explicit user holds with consumers and end conditions.

### Ending conversation cleanup

Use `ending_conversation.py` or native conversation deletion/archive tools only for the exact operation the user explicitly requests. Leave session files and databases untouched.

## Isolation and privacy

- Use exact project identity for recall and writes. Store project decisions with that project and only explicitly general preferences with the shared owner.
- Save concise facts and project-relative files. Exclude raw prompts, transcripts, reasoning, credentials, absolute host paths and other projects' content.
- Use the memory writer for events and read back actual saves from Obsidian. Keep probes in isolated task Cache with test data.
- Keep durable memory, dated outcomes, pending queues, coverage and memory pointers out of Codex storage, project Cache and project guidance. The bounded ignored `cache/current.json` inventory holds only current operational Cache state.

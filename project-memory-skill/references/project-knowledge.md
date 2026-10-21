# Central project knowledge

Use this contract when recalling code context or consolidating a completed outcome. Keep addressable knowledge together; addressability does not require one file per entity.

## Storage and identity

- `Projects/<owner>/Memory.json` holds the project's structured current knowledge and consolidation state. `Knowledge.md` is its readable view, not a competing store. Keep historical evidence in the existing `AI Memory/events.jsonl`.
- Scope every entry by registered project identity, module, project-relative file, and symbol where relevant. Use a qualified method name or signature when a short name is ambiguous. Omit inapplicable scopes rather than inventing empty module or method records.
- Record architecture and ownership changes at the project or module level. Record a method only when its responsibility, contract, dependency, or important constraint adds durable value. Link related entries instead of copying their content.
- `scope=project` means a stable contract that applies across this project: identity, architecture, shared ownership or repository-wide policy. Membership in a project alone does not qualify. Feature rules and user preferences belong to their module; a single task's release/test/cleanup snapshot belongs to scoped continuity or history. Audit misclassified entries through guarded retirement plus narrower replacement, preserving their original evidence and dates.
- Entry status is `current` or `retired`. Preserve provenance and verification status; superseded versions stay in history, while stale or unknown evidence must remain distinguishable during recall. A rename, move, or deletion explicitly retires the old exact scope and updates relationships. Do not present removed methods as current.

## Precise recall

Use the owning Skill's `scripts/project_knowledge.py`:

```text
project_knowledge.py recall --project-root ROOT --vault VAULT --module MODULE --file relative/path --symbol Qualified.Method --query TEXT
```

Ordinary recall requires at least one task selector: module, file, symbol, or meaningful query. Filter types combine with AND. Method recall requires `--module`, exactly one `--file`, and one or more `--symbol` values from that file. Repeat `--file` only when no symbol filter is used. An unfiltered `--include-project-context` explicitly selects project facts and navigation synthesis, never an arbitrary sample of module facts. Project identity is bound to the real root, with registered aliases only; text queries never widen it to other projects. A missing index or owner conflict skips recall without a broad event-store fallback.

Memory is selectable project evidence, not ambient user history. Current contracts and useful dated attempts remain stored, but only the exact owner and task scope enter ordinary context. During a requested migration or isolation audit, replace obsolete whole-page, local-memory and event-only instructions in the actual project route; a new sentence saying it overrides contradictory commands does not retire those commands. Preserve useful legacy facts in canonical history before removing a duplicate memory layer. Already injected session content cannot be revoked by changing a file or setting; future sessions must use the effective disabled native-memory configuration and the scoped reader.

Read the smallest useful set of current entries and directly relevant relationships. Ordinary recall includes only selected facts and a same-module parent, never automatic project-wide parents or synthesis. Add `--include-project-context` only when the task requires project architecture or crosses ownership boundaries. Cross-project relations remain unloaded pointers. A no-match or stale result calls for the owning source, never a whole Knowledge page, Codex-local memory or unscoped history fallback. Consult bounded history only to resolve a decision, conflict, or provenance question. A missing entry means inspect the source, not create an empty memory file.

When a module name is unknown or has changed, use `project_knowledge.py scopes --project-root ROOT --vault VAULT --query TASK_TERMS` or `--file RELATIVE_FILE`. It returns at most five exact-owner module/file/symbol pointers, no summaries, facts or history. Select the relevant pointer and repeat ordinary recall with those exact selectors. Discovery does not check source freshness or make a pointer current authority; the subsequent recall still excludes stale facts. Do not guess module aliases, auto-import another project or read an entire generated page to find a name.

Use a source-owned file or distinctive task terms for ambiguous words (for example, `Normal Mask` rather than `normal`). Ranking is a navigation aid, not semantic proof; never automatically accept the first pointer. Declared files rank above supporting evidence paths, whose entries may describe a broader task.

Scope discovery prioritizes a declared file, module or symbol and the entry's topic over supporting source hashes. Supporting files are evidence dependencies, not ownership declarations; their pointers are labeled `supporting_source` and must not select a module merely because a broad evidence bundle mentions that file.

Fresh source and the user's current instructions prevail. Source hashes captured by the originating task's handoff, or explicitly provided from its verified source, support bounded freshness checks at recall. Stale entries are excluded. Methods with absent source hashes return separately as unverified pointers; their claims are never eligible current context. Unreadable source evidence also excludes an entry from current context. A matching hash is source identity, not runtime proof. Verify consequential current claims against the affected source or actual output before relying on them; report unknown evidence and historical claims as such.

Capture minimal per-entry source files and dependencies supporting that claim. Share outcome-level hashes only when every entry depends on all those files; explicit per-entry hashes override that shared bundle. Never automatically trim old hashes or rehash old claims to make a stale entry current.

Relations point to `{project, module, file?, symbol?, relation, reason}` and do not automatically load target content. For a cross-project analogy, explicitly select the source project and relevant reference link or comparison scope. Keep the borrowed material labeled as a reference with its source identity; independently establish whether it applies here. It never becomes this project's current contract merely because names or code resemble each other.

## Project, task and underlying logic

The retrieval chain is project → relevant task memory → underlying logic. Isolation prevents unrelated context; it must not prevent useful transfer between projects with the same causal principle. First identify the current problem, constraints and exact task scope. Then follow an established principle, not a shared word or project name.

Reuse the existing relationship schema: a task entry links to an explicitly shared principle with `{project: SHARED_OWNER, module: logic.performance.bounded-parallelism, relation: applies-logic, reason: applicability}`. The principle is an ordinary scoped entry under its declared owner, with transferable rule, applies/avoid conditions and evidence limits; concrete implementations and dated attempts remain with their original project. Record implementation differences in the case's existing decisions/risks. No duplicate logic database or per-task file is needed.

```text
project_knowledge.py logic --project-root ROOT --vault VAULT --module TASK_MODULE
project_knowledge.py logic --project-root ROOT --vault VAULT --module TASK_MODULE --principle-owner SHARED_OWNER --principle logic.performance.bounded-parallelism
```

The command requires exact project identity and task selectors. It derives up to three principles from selected current task entries/parents, or uses one explicitly selected principle when the task has no saved match. It reads bounded relationship metadata across owners and returns at most five reference pointers, at most two per owner, without foreign claims, source reads or history. Ordinary recall remains local. Missing/retired principles do not select cases; invalid owners and bounds are explicit limitations. Keyword discovery may suggest candidates but never writes a same-logic relationship automatically.

Select a relevant principle and case pointer, resolve its exact registered project, and apply that project's AI-index gate before source inspection. Use scoped recall for current reference facts. If stale, retain the pointer; an explicit provenance question may read its exact dated event as historical evidence, never as a current implementation or new benchmark. Compare **common principle → applies/avoid conditions → implementation differences → source dates and proof limits** before adaptation. For parallelism, independent I/O may overlap while shared commits stay ordered; worker counts, APIs, lifetimes and measured speedups do not transfer automatically. No-match never authorizes unrelated project facts or whole pages.

The readable view links an exact memory anchor only when that anchor exists. Otherwise it shows the source scope beside the existing owner page, or as plain text when the owner page is absent; it never invents a target entry.

## Registered root aliases

After confirming that a moved or second-machine checkout belongs to the same repository, use `project_knowledge.py register-alias --project-root ROOT --vault VAULT --expected-owner OWNER --expected-project-key STORED_KEY --expected-index-sha256 SHA256`. The root must be registered to that exact owner. Read the stored key and SHA from that owner's current `Memory.json`; a changed index requires a fresh read. The guarded writer retains the primary key, entries, history, maintenance and readable knowledge, adds only the current registered root key, and verifies readback. Repeating an existing alias does not write. Owner conflicts, unregistered roots, malformed aliases and links reject; never relabel an index by name or edit its keys manually.

## Consolidation in Ending

Every memory Ending reviews touched entries and their direct relationships. Merge the prior scoped entry with established new facts into complete current truth, retain useful decisions and limitations, and remove duplication while preserving history. A raw changelog is not a current entry. A method entry never overwrites its module's unrelated facts. Ending does not collect fresh source hashes or upgrade old claims to verified.

Sparse updates preserve omitted reasons, results, decisions, risks, relationships and retirement status within the same exact entry. Use explicit per-entry values, including empty lists or empty optional text, to reconcile or clear them. Keep prior problems and user corrections with the established solution, unresolved items and next steps; summary omission preserves the existing summary. Outcome-level defaults seed new structured entries without erasing an existing entry's continuity. Preparation merges the full current entry before passing it to Ending, and the writer records that merged entry in the canonical history before updating the index.

When a claim changes, omitted verification and source evidence are cleared rather than inherited as proof of the new claim. Supply the originating task's new verification status and evidence explicitly; source hashes alone establish source identity, not a passed behavior check. The last verified version remains in its original history event. A changed entry invalidates current project synthesis unless the same update supplies a new synthesis; the old synthesis remains historical.

The completed outcome may contain `memories`, a list of scoped entries with `scope` (`project`, `module`, `method`, or `document`), `module`, optional `file`/`symbol`, `summary`, and applicable `reason`, `result`, `decisions`, `risks`, `verification_status`, `verification`, and `relations`. Use explicit method entries for precise contracts. Legacy module outcomes remain accepted; a legacy `symbols` list is meaningful only for an unambiguous single file. Exact retirement uses the supported writer's `retired` status instead of silently erasing history.

Project synthesis is due immediately for nonempty current knowledge without valid synthesis, and after 20 distinct writes or 30 days. Empty or fully retired knowledge needs no summary. An empty outcome still checks exact-owner cadence; an unchanged complete owner skips without rewriting events, indexes or generated views. These thresholds are implementation constants. Replayed outcomes do not advance the write count. Refresh due synthesis in the same Ending, with no automation or extra task chain.

Synthesis reviews established architecture, module responsibilities, contracts, unresolved issues and relationships. Supply `consolidation: {summary, relations?, entry_ids?}`; the writer auto-captures eligible current contributors unless exact scope IDs are explicitly selected. The bounds are 50 contributing entries and 64 distinct source files; exceeding them returns pending without silent truncation. Stale, retired, unreadable or hashless method contributors are excluded or refused. Partial and unverified inputs retain their limits. Legacy unknown contributors require refresh; source changes withhold old synthesis even beside a fresh selected entry. Recalled synthesis has `eligible_current_context=false` and is navigation only. Cross-project links remain references.

For synthesis alone, pass an outcome containing only `consolidation` and optional `expected_index_sha256` to `scripts/ending_memory.py --outcome JSON --project-root ROOT --vault VAULT`. No fictional files, module changes or verification are required: the writer records a documentation event with not-run proof, individual contributor IDs and canonical provenance, preserving the original entries and dates. A reviewed draft's SHA is checked under the Ending and project locks before its event is written; a stale preimage returns pending without overwriting. Main result verification remains owned by the originating task. Memory completion requires a fresh same-owner readback with `maintenance_due=false`; pending memory never blocks resource cleanup.

Capture useful established outcomes after failure or pause as well as successful completion: save the actual blocker, partial or failed result and next step, with the evidence available at that boundary. Preserve the last verified version as history; never infer new proof from a summary.

Update through the supported writers and read back both the saved event and central knowledge. Direct `apply_entries` writes require an existing canonical event whose project exactly matches the current registered owner. Keep ordinary reads scoped after consolidation; periodic synthesis is not a reason to load the entire vault on every task. Skip empty scaffolding and per-task, per-module, or per-method note proliferation.

For reviewed index repairs, pass the exact preimage SHA256 as `expected_index_sha256` to `apply_entries`; it checks under the project lock and rejects concurrent changes. Reconcile a proven owner split using the repository's declared owner and preserve original evidence and verification limits. When the user requests removal, verify the handoff and updated references, then delete the unused secondary owner and legacy copies instead of keeping another archive. Keep useful chronology in the canonical event store; never choose conflicting current claims by timestamps alone.

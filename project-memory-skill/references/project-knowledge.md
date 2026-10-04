# Central project knowledge

Use this contract when recalling code context or consolidating a completed outcome. Keep addressable knowledge together; addressability does not require one file per entity.

## Storage and identity

- `Projects/<owner>/Memory.json` holds the project's structured current knowledge and consolidation state. `Knowledge.md` is its readable view, not a competing store. Keep historical evidence in the existing `AI Memory/events.jsonl`.
- Scope every entry by registered project identity, module, project-relative file, and symbol where relevant. Use a qualified method name or signature when a short name is ambiguous. Omit inapplicable scopes rather than inventing empty module or method records.
- Record architecture and ownership changes at the project or module level. Record a method only when its responsibility, contract, dependency, or important constraint adds durable value. Link related entries instead of copying their content.
- Entry status is `current` or `retired`. Preserve provenance and verification status; superseded versions stay in history, while stale or unknown evidence must remain distinguishable during recall. A rename, move, or deletion explicitly retires the old exact scope and updates relationships. Do not present removed methods as current.

## Precise recall

Use the owning Skill's `scripts/project_knowledge.py`:

```text
project_knowledge.py recall --project-root ROOT --vault VAULT --module MODULE --file relative/path --symbol Qualified.Method --query TEXT
```

Module, file, symbol, and query are optional filters; filter types combine with AND. Method recall requires `--module`, exactly one `--file`, and one or more `--symbol` values from that file. Repeat `--file` only when no symbol filter is used. Project identity is bound to the real root, with registered aliases only; text queries never widen it to other projects. A missing index or owner conflict skips recall without a broad event-store fallback.

Read the smallest useful set of current entries and directly relevant relationships. Include project architecture when the task crosses ownership boundaries or changes structure. Consult bounded history only to resolve a decision, conflict, or provenance question. A missing entry means inspect the source, not create an empty memory file.

Fresh source and the user's current instructions prevail. Source hashes captured by the originating task's handoff, or explicitly provided from its verified source, support bounded freshness checks at recall. Stale entries are excluded. Methods with absent source hashes return separately as unverified pointers; their claims are never eligible current context. Unreadable source evidence also excludes an entry from current context. A matching hash is source identity, not runtime proof. Verify consequential current claims against the affected source or actual output before relying on them; report unknown evidence and historical claims as such.

Relations point to `{project, module, file?, symbol?, relation, reason}` and do not automatically load target content. For a cross-project analogy, explicitly select the source project and relevant reference link or comparison scope. Keep the borrowed material labeled as a reference with its source identity; independently establish whether it applies here. It never becomes this project's current contract merely because names or code resemble each other.

## Registered root aliases

After confirming that a moved or second-machine checkout belongs to the same repository, use `project_knowledge.py register-alias --project-root ROOT --vault VAULT --expected-owner OWNER --expected-project-key STORED_KEY --expected-index-sha256 SHA256`. The root must be registered to that exact owner. Read the stored key and SHA from that owner's current `Memory.json`; a changed index requires a fresh read. The guarded writer retains the primary key, entries, history, maintenance and readable knowledge, adds only the current registered root key, and verifies readback. Repeating an existing alias does not write. Owner conflicts, unregistered roots, malformed aliases and links reject; never relabel an index by name or edit its keys manually.

## Consolidation in Ending

Every memory Ending reviews touched entries and their direct relationships. Merge the prior scoped entry with established new facts into complete current truth, retain useful decisions and limitations, and remove duplication while preserving history. A raw changelog is not a current entry. A method entry never overwrites its module's unrelated facts. Ending does not collect fresh source hashes or upgrade old claims to verified.

The completed outcome may contain `memories`, a list of scoped entries with `scope` (`project`, `module`, `method`, or `document`), `module`, optional `file`/`symbol`, `summary`, and applicable `reason`, `result`, `decisions`, `risks`, `verification_status`, `verification`, and `relations`. Use explicit method entries for precise contracts. Legacy module outcomes remain accepted; a legacy `symbols` list is meaningful only for an unambiguous single file. Exact retirement uses the supported writer's `retired` status instead of silently erasing history.

Project synthesis becomes due after 20 distinct writes since the last synthesis, or 30 days since the last synthesis (the first write before any synthesis). These thresholds are implementation constants, with no CLI configuration. Replayed or duplicate outcomes do not advance the write count. Check due status and perform synthesis in the first Ending run after it becomes due, with no new automation or task chain.

Synthesis reviews the project's current architecture, module responsibilities, key contracts, unresolved issues, and existing relationships. Supply `consolidation: {summary, relations?}` with a coherent current summary and meaningful links; preserve uncertain facts as uncertain. Link established related knowledge without treating an inferred relationship as a verified dependency. Cross-project connections remain explicit reference links and do not merge project stores.

Update through the supported writers and read back both the saved event and central knowledge. Keep ordinary reads scoped after consolidation; periodic synthesis is not a reason to load the entire vault on every task. Skip empty scaffolding and per-task, per-module, or per-method note proliferation.

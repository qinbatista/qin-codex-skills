# Automatic project AI index

This global function maintains each project's navigation and stable rules. Run it at project task start or resume, when the user changes project intent or source ownership, and before task completion. It is part of the agent's workflow, not an OS watcher or scheduled job. Do not wait for another request to maintain the index.

## One project owner

Every editable project owns `.agents/skills/ai-index/SKILL.md`. This is a project Skill, never a global installation or plugin Skill. Existing domain/plugin Skills remain their own authorities; the index links to them. Resolve the actual project root first. Respect explicit read-only boundaries, user holds and repository permissions; report an unavailable index instead of writing elsewhere. A projectless conversation has no index to create.

Keep root `AGENTS.md` a concise project contract: purpose, overall structure, critical boundaries and conventions, definition of done, and one link to the project index. Put detailed module rules in the index's focused documents or their existing authoritative references. Avoid adding nested `AGENTS.md` files as navigation. Preserve existing nested scopes and tool-required files; consolidate only when their rules, precedence and consumers can be preserved. Never silently delete or flatten them.

The project index contains:

- `SKILL.md`: frontmatter `name: ai-index`, when/how to select a route, and a link to `index.json`.
- `index.json`: the single route map, with project-relative paths. `rules` declares `repository`, `structure` and `verification` documents. `modules` declares each `id`, short `summary`, `document`, `sources`, and `dependencies` with a module ID and reason.
- Focused Markdown documents for repository/asset ownership, code placement, verification, and each meaningful module. Use a folder/sub-index only when a module needs it; do not create a document for every function.

Repository/asset rules cover Git and publication boundaries, canonical inputs/assets, runtime data, generated artifacts, secrets and disposable support. Structure rules state responsibilities and where new code belongs. Each module document names its entry files/symbols, contracts, exclusions, justified dependencies and relevant test owner. Link existing rules instead of copying whole Skills, prompts or source files. Store task history, failures, results and changing inventories in their existing memory/resource owners, not these instructions.

## Start, change and finish

1. Read root guidance, then run `project_ai_index.py inspect --project-root ROOT --phase start`. Pass known task/Git changed files with repeated `--changed-path PATH`. Read the small route map and select only the relevant rule/module documents. The helper returns paths and hashes, not whole source files.
2. If missing, use the bounded guidance/path inventory to review existing `AGENTS.md` files and discover actual source entry points. Build a concise root contract and the project index from verified ownership and user instructions. An existing index is reused; a legacy or incomplete format is reconciled without replacing useful authored content blindly. Do not leave an empty scaffold and call it indexed.
3. Compare current user intent and the affected source structure with those instructions. Accepted enduring project ideas, changed responsibilities, moved/removed entry points, new modules and corrected constraints trigger a scoped update automatically. An idea still under discussion stays a proposal; do not write it as implemented behavior. A successful run, error log or one-off workaround alone does not create a rule.
4. On a route miss, first search names/symbols in the likely owner, then expand one justified dependency at a time. Repair the verified route. For a cross-module task, load each necessary owner explicitly. Never recursively read every linked document or scan all code because the index exists.
5. Before final verification and authorized Git delivery, run the same inspection with `--phase end` and the task's changed paths. Reconcile the root and index, validate links/contracts and read the resulting documents. An unchanged project produces a no-op; do not rewrite files or add timestamps merely to mark a check. Include task-owned guidance changes in the same scoped delivery.
6. Ending performs a residual check through this same owner, including when memory has no new facts. It may update only root `AGENTS.md` and the project index from established intent and fresh scoped evidence. It never changes product code, global/plugin Skills, runs product tests/builds, or publishes. Preserve concurrent edits. Record any residual changes as local guidance changes, with delivery pending unless separately authorized; the parent never waits or resumes. If Ending is unavailable, finish this step inline.

Structural validity is not semantic acceptance: a valid map can still describe the wrong owner. Compare the relevant route with actual source and user intent. Keep unknown contracts explicit. Source evidence must support the claim; a fresh hash is not proof of runtime correctness.

## Unrelated context and redesign

When a route repeatedly pulls unrelated responsibilities, identify the exact files/rules, explain the unnecessary dependency, and propose a concrete module split to the user. Continue independent work, but obtain the user's direction before a structural code refactor. An explicit decision to retain the current structure permits bounded work without repeating the same warning. Legitimate cross-module dependencies and file length alone do not establish a design defect. The index update itself does not authorize source restructuring.

## Portable helper

Use the installed Management Skill's `scripts/project_ai_index.py` with the host's Python 3 interpreter (`python3 -B` on macOS/Linux, `py -3 -B` on Windows). Resolve installation paths rather than hardcoding a home directory.

```text
project_ai_index.py inspect --project-root ROOT --phase start --changed-path src/feature.py
project_ai_index.py route --project-root ROOT --module feature
project_ai_index.py check --project-root ROOT
project_ai_index.py apply --project-root ROOT --plan PLAN_JSON --work-dir EXTERNAL_RUN
project_ai_index.py inspect --project-root ROOT --phase end --changed-path src/feature.py
```

The agent authors a reviewed plan in the current [external task run](../../workflow-skill/references/project-cache-artifact-policy.md). The helper checks exact project identity, evidence hashes, target preimages, path containment and the proposed map before writing. It cannot infer semantics or override permissions. Plan shape:

```json
{
  "schema_version": 1,
  "project_root": "<resolved project root>",
  "evidence": {"src/feature.py": "<sha256>"},
  "files": [
    {"path": "AGENTS.md", "expected_sha256": "<sha256>", "content": "<reviewed complete document>"},
    {"path": ".agents/skills/ai-index/SKILL.md", "expected_sha256": null, "content": "<reviewed complete skill>"}
  ]
}
```

Include the manifest and required module/rule documents in a bootstrap plan. `expected_sha256: null` means the target must not exist; `content: null` removes only an obsolete index document after its references are reconciled. Existing files require their exact inspected hashes. Evidence binds the source files supporting a change, including non-target guidance used during consolidation. Do not store this plan, hashes, receipts or run state in the maintained index.

On stale evidence or concurrent changes, reread only the affected scope and rebuild the plan if its meaning is still established. Otherwise leave that update pending with the concrete cause. Preserve recoverable state under its external owner; do not overwrite a newer writer or manufacture a successful check. Reread the final root and selected module documents to verify preserved constraints, useful routing and absence of unrelated context. Routine index maintenance does not reinstall or publish global Skills.

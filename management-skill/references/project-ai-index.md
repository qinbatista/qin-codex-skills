# Automatic project AI index

This global function maintains each project's navigation and stable rules. Run it at project task start or resume, when the user changes project intent or source ownership, and before task completion. It is part of the agent's workflow, not an OS watcher or scheduled job. Existing indexes receive automatic maintenance; first creation requires the startup consent below.

The always-loaded global `AGENTS.md` must carry the startup gate; a discoverable Skill body alone cannot enforce entry. Management's explicit `install-global-agents --startup-only` installs that block with a recoverable backup while preserving other instructions. Ordinary deployment reports activation gaps, including a global override. Verify a fresh session and the actual target project; a previously running session or a successful helper test alone does not prove that the question appeared.

## One project owner

Every editable project owns one project-local AI index. Prefer existing `skills/ai-index/SKILL.md`; otherwise reuse existing `.agents/skills/ai-index/SKILL.md`. Directory presence selects the owner, including partial or malformed entries: a visible index must not silently fall back to a legacy index. Never recreate `.agents` after an explicitly visible-source migration. With neither directory present, retain the first-bootstrap consent gate; the helper's default bootstrap location remains the legacy path unless the user establishes a visible owner. This is a project Skill, never a global installation or plugin Skill. Existing domain/plugin Skills remain their own authorities; the index links to them. Resolve the user's actual target project first, even when the chat's working directory is another repository. A fixture, snapshot or isolated test copy cannot satisfy maintenance of that live target. Respect explicit read-only boundaries, user holds and repository permissions; report an unavailable index instead of writing elsewhere. A projectless conversation has no index to create.

Keep root `AGENTS.md` a concise project contract: purpose, overall structure, critical boundaries and conventions, definition of done, and one link to the project index. Put detailed module rules in the index's focused documents or their existing authoritative references. Avoid adding nested `AGENTS.md` files as navigation. Preserve existing nested scopes and tool-required files; consolidate only when their rules, precedence and consumers can be preserved. Never silently delete or flatten them.

The project index contains:

- `SKILL.md`: frontmatter `name: ai-index`, when/how to select a route through the compact module menu, and a link to `index.json` for maintained metadata rather than routine full-manifest reading.
- `index.json`: the single route map, with project-relative paths. `rules` declares `repository`, `structure` and `verification` documents. `modules` declares each `id`, short `summary`, `document`, `sources`, and `dependencies` with a module ID and reason. Optional `code_targets` locate reviewed methods and key-line anchors under that module.
- Focused Markdown documents for repository/asset ownership, code placement, verification, and each meaningful module. Use a folder/sub-index only when a module needs it; do not create a document for every function.

Repository/asset rules cover Git and publication boundaries, canonical inputs/assets, runtime data, generated artifacts, secrets and disposable support. Structure rules state responsibilities and where new code belongs. Each module document names its entry files/symbols, contracts, exclusions, justified dependencies and relevant test owner. Link existing rules instead of copying whole Skills, prompts or source files. Store task history, failures, results and changing inventories in their existing memory/resource owners, not these instructions.

## Start, change and finish

1. Before broad project reading, run `project_ai_index.py inspect --project-root ROOT --phase start`. Ask for bootstrap consent only when the project has no AI index at all: the helper returns `approval_required` only when both `skills/ai-index` and `.agents/skills/ai-index` are absent, after a presence check without reading root guidance, inventorying directories or reading source. Immediately ask whether the user agrees to read the necessary rules and create this project's first AI index. Wait for that answer before discovery or first creation; a project task alone is not bootstrap consent. Existing index directories, partial entries and malformed/empty manifests are repair cases, not new consent gates. Validate them, preserve authored guidance and repair only the relevant scope automatically. Explicit read-only boundaries still apply. Already injected context cannot be unread, but does not justify additional scanning before first-bootstrap consent.
   `required_action: ask_user` and `blocks_project_work: true` are an instruction to present the returned question in the user's language, not an ordinary command failure to bypass. Use an available question tool; if none is available, ask plainly and end the turn. This gate also applies to read-only questions and when the requested target differs from the working directory. Check before Git, project-memory recall or delegation, so another entry cannot read the unindexed project first.
2. If the user agrees, rerun with `--allow-bootstrap`, use the bounded guidance/path inventory, and review existing `AGENTS.md` scopes and actual source entry points. Build and apply a concise root contract and useful project index in the actual editable project, then verify through a fresh helper readback. A test-only bootstrap or empty scaffold is incomplete. If declined, deferred or unanswered, leave creation pending and do not scan merely to prepare it. Ask again at each later project start/resume only while no index exists; do not repeatedly interrupt the same interaction or create background reminders. Reuse explicit approval for the same continuing bootstrap, never another project. Keep approval in current task context/plan, not a persistent acceptance/decline marker. When any index exists, reuse and repair it without another bootstrap question. Add modules, routes, documents and sub-indexes automatically as established ownership requires. Review legacy/incomplete authored formats instead of replacing them blindly. A valid unchanged index needs no write.
3. Compare current user intent and the affected source structure with those instructions. Accepted enduring project ideas, changed responsibilities, moved/removed entry points, new modules and corrected constraints trigger a scoped update automatically. An idea still under discussion stays a proposal; do not write it as implemented behavior. A successful run, error log or one-off workaround alone does not create a rule.
4. On a route miss, first search names/symbols in the likely owner, then expand one justified dependency at a time. Repair the verified route. For a cross-module task, load each necessary owner explicitly. Never recursively read every linked document or scan all code because the index exists.
5. Before final verification and authorized Git delivery, run the same inspection with `--phase end` and the task's changed paths. Reconcile the root and index, validate links/contracts and read the resulting documents in their actual owner. Report local source changes, installation and publication separately; successful tests in another folder cannot imply target delivery. An unchanged project produces a no-op; do not rewrite files or add timestamps merely to mark a check. Include task-owned guidance changes in the same scoped delivery.
6. Ending performs a residual check through this same owner, including when memory has no new facts. It may update only root `AGENTS.md` and the project index from established intent and fresh scoped evidence. Missing bootstrap consent stays pending; Ending cannot infer it from maintenance authority or bypass the startup question. It never changes product code, global/plugin Skills, runs product tests/builds, or publishes. Preserve concurrent edits. Record any residual changes as local guidance changes, with delivery pending unless separately authorized; the parent never waits or resumes. If Ending is unavailable, finish this step inline.

Structural validity is not semantic acceptance: a valid map can still describe the wrong owner. Compare the relevant route with actual source and user intent. Keep unknown contracts explicit. Source evidence must support the claim; a fresh hash is not proof of runtime correctness.

## Code navigation

For every local code change in every language, including tests, tools and temporary scripts, use module → file → method or key-line anchor → necessary relationships; reuse the same method routes for read-only code investigations. Apply [Code's writing philosophy](../../code-skill/references/code-writing-philosophy.md) to the actual method boundary. Resolve the task's main target once with `route --module ID --target TARGET` before its first source-body read when that target exists. Then read necessary callers, callees and tests directly by their already-known file/symbol or range; do not require another route call for every pointer. Never recursively preload all related targets or restart broad `def`/`source` discovery after locating the owner. Recall exact project/module/file/symbol memory; a missing entry is a normal skip. The route starts the investigation; establish the affected operation's inputs, state transitions, outputs and failure handling before changing it.

Start with the affected method or fragment and read the complete necessary logic. A bounded excerpt, including the default ±12 lines, is not a complete method: read through the method's end and required controlling context before changing it or claiming its full behavior. Merge overlapping ranges from the same file and batch independent known reads in one request. If necessary methods cover most of one cohesive file, read that file once instead of repeating overlapping fragments; this does not authorize loading unrelated files or whole modules. Reuse already-read unchanged Skills and source fragments within the task; reread only relevant regions after their source changes. Query exact symbols and necessary callers in identified files, expanding for unresolved contracts. For an absent, stale or ambiguous target, perform one bounded symbol/anchor lookup in the likely owner and repair the verified route. Correct, complete understanding and modification take priority over reducing tokens or reads; there is no token, method-count or reading-line quota, nor a helper-call ritual before each method.

Evaluate adherence on a real affected case: the route reaches the intended method, the necessary logic was actually read, edits stay with their owner, any new method has a justified boundary, and the affected behavior passes a real test. Structural validation or a mechanical violation scan alone cannot prove that the AI followed this workflow. Keep the evidence and report proportional to the change; no separate lengthy checklist is required.

Maintain a compact `code_targets` list in the module's manifest entry for the code actually touched or needed as a stable entry. Each target has `id` (unique lowercase hyphenated within its module), `file` (exact project-relative source file owned by `sources`), `symbol` (qualified method/function name, or a descriptive key-block name), `anchor` (one unique trimmed source line), `summary` (responsibility and essential input/output or state contract), and optional `related` entries with `module`, `target` and a concrete `reason`. Use relationships for necessary callers/callees, state owners and affected tests; test methods are ordinary targets. Give overloads or repeated signatures an actually unique local anchor rather than guessing from a symbol name. No language parser or automatic call-graph inference is assumed.

```json
"code_targets": [{
  "id": "read-content",
  "file": "src/player.py",
  "symbol": "Player.read_content",
  "anchor": "def read_content(self, location, browser):",
  "summary": "Open the selected browser, read content and release the owned session; return content or propagate failure.",
  "related": [{"module": "player-tests", "target": "read-content-failure", "reason": "Checks session release when content reading fails."}]
}]
```

Register only targets that exist; referenced related targets must also be declared in their owners. Keep one module document for explanatory logic, not a document per method. Do not copy source bodies, persistent line ranges, source hashes, task outcomes or execution traces into the index. Stable navigation and contracts belong here; dated decisions, failures and source-bound verification remain in [Project Memory](../../project-memory-skill/SKILL.md). Temporary code follows the same reading/writing discipline but its disposable paths never become maintained routes; index its maintained producer or test owner when useful.

Start with `route --project-root ROOT`: it returns only each module's `id`, `summary` and `document`, without source content or the full manifest. Choose from this compact menu instead of reading all of `index.json`. `route --module ID` then lists that module's target summaries without reading source content. `--target` requires `--module`; without it the helper returns `needs_review`. Every route retains the missing-index consent gate.

`route --module ID --target TARGET` opens only the chosen file (at most 1 MiB), resolves its unique exact-line anchor against current bytes, and returns the current line, source hash and bounded excerpt (12 lines each side by default; `--context-lines 0..40`, at most 16 KiB of excerpt text). The hash and line numbers are transient read evidence, not runtime acceptance. Related entries are pointers only and do not recursively load source. Missing/ambiguous anchors, unknown targets and oversized sources stay `needs_review`; use a bounded symbol lookup and repair the verified route before editing. `inspect`/`check` validate metadata and paths without reading source bodies, so structural success alone cannot prove that anchors remain current.

After changing code, reconcile touched targets, contracts, anchors and necessary relationships from the actual final source before delivery. Remove old targets/references for renamed, moved or deleted code, and verify each changed target through a fresh selected route. Use guarded `apply` with evidence for the selected source files. Existing indexes without targets remain valid; enrich the touched scope incrementally, never pre-index every function or rescan unrelated code. Instructions and navigation must match the delivered source; memory cannot excuse a stale route.

## Unrelated context and redesign

When mixed responsibilities, duplicated variants or trivial forwarding chains obscure an operation, identify the exact methods and coupling. Propose the resulting module/method structure, what stays together, what becomes a parameter or an independent responsibility, how this clarifies ownership and the complete logic, and the behavior checks that will verify it. Ask whether to refactor before an otherwise unauthorized structural change; continue independent requested work. An explicit decision to retain the current structure permits bounded work without repeated warnings. Legitimate dependencies and method/file length alone do not prove a defect. After an authorized refactor, verify preserved behavior and demonstrate that the new routes reach the affected code and tests. The index update itself never authorizes source restructuring.

## Portable helper

Use the installed Management Skill's `scripts/project_ai_index.py` with the host's Python 3 interpreter (`python3 -B` on macOS/Linux, `py -3 -B` on Windows). Resolve installation paths rather than hardcoding a home directory. Keep source routes project-relative and document links relative to their containing file. Machine-local absolute paths and file URIs cannot be saved as local links.

Checks follow linked Markdown only inside the project index, including focused subdocuments, with cycle protection and a 256-document bound. They validate every proposed guidance document before writing and return guidance hashes without emitting source contents. Links to source or other Skills are checked for existence without recursively reading those files.

```text
project_ai_index.py inspect --project-root ROOT --phase start --changed-path src/feature.py
project_ai_index.py inspect --project-root ROOT --phase start --allow-bootstrap
project_ai_index.py route --project-root ROOT
project_ai_index.py route --project-root ROOT --module feature
project_ai_index.py route --project-root ROOT --module feature --target read-content --context-lines 12
project_ai_index.py check --project-root ROOT
project_ai_index.py apply --project-root ROOT --plan PLAN_JSON --work-dir PROJECT_CACHE_RUN
project_ai_index.py inspect --project-root ROOT --phase end --changed-path src/feature.py
```

The agent authors a reviewed plan in the current [project Cache task run](../../workflow-skill/references/project-cache-artifact-policy.md). The helper checks exact project identity, evidence hashes, target preimages, path containment and the proposed map before writing. It cannot infer semantics or override permissions. Plan shape:

```json
{
  "schema_version": 1,
  "project_root": "<resolved project root>",
  "bootstrap_approved": true,
  "evidence": {"src/feature.py": "<sha256>"},
  "files": [
    {"path": "AGENTS.md", "expected_sha256": "<sha256>", "content": "<reviewed complete document>"},
    {"path": ".agents/skills/ai-index/SKILL.md", "expected_sha256": null, "content": "<reviewed complete skill>"}
  ]
}
```

Include the manifest and required module/rule documents in a bootstrap plan. Set `bootstrap_approved: true` only after explicit user agreement; the helper refuses first creation when no index directory exists without it. Existing indexes need no new approval field for expansion or repair, including partial indexes. `expected_sha256: null` means the target must not exist; `content: null` removes only an obsolete index document after its references are reconciled. Existing files require their exact inspected hashes. Evidence binds the source files supporting a change, including non-target guidance used during consolidation. Do not store this plan, hashes, receipts or run state in the maintained index.

On stale evidence or concurrent changes, reread only the affected scope and rebuild the plan if its meaning is still established. Otherwise leave that update pending with the concrete cause. Preserve recoverable state under its external owner; do not overwrite a newer writer or manufacture a successful check. Reread the final root and selected module documents to verify preserved constraints, useful routing and absence of unrelated context. Routine index maintenance does not reinstall or publish global Skills.

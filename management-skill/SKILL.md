---
name: management-skill
description: "Automatically maintain project AI indexes and concise root guidance; maintain, install or publish global skills, and repair legacy Skill directories and references."
---

# Skill Management

Before any file write, apply the [external artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). All task support belongs outside project directories and Codex storage from its first write. Source, installed updates and retained recovery backups keep their declared owners; inspect exact paths and the Git index before committing.

Use for automatic project AI-index maintenance and requested global Skill maintenance, installation or publication. Ensure the Obsidian vault through Project Memory and read related project memory; skip absent matching records and isolate other projects. Briefly explain the intended steps before execution.

## Maintain

Each skill's source directory is its owner. Global skills describe reusable concepts and preferences; project skills own concrete domain implementations. Apply the authoring rules below when creating or updating either kind.

### Automatic project AI index

Use [the project AI-index function](references/project-ai-index.md) at project start/resume, on established intent/structure changes, and at finish. Ask for agreement only when the project has no AI index at all, before reading the necessary rules and creating its first index. Once the index exists, automatically add modules, routes, documents and sub-indexes or repair incomplete/stale guidance within editable scope; these additions need no new index-creation question. Its portable `scripts/project_ai_index.py` validates routes and applies reviewed, source-bound updates to root `AGENTS.md` and the project's existing AI index (`skills/ai-index` first, otherwise `.agents/skills/ai-index`). The project index is never installed globally or inside a plugin. Task Analyze, Workflow and Ending invoke this same owner and consent boundary.

For every local code edit, including tests, use [code navigation](references/project-ai-index.md#code-navigation): module, exact file, reviewed method/key-line target, scoped memory and only necessary relationships. Maintain touched stable targets against current source; return bounded excerpts on selection and keep implementation history in Project Memory. Code owns cohesive method boundaries and deliberate extraction.

### Authoring rules

Keep Skills focused on stable rules, decision criteria, essential workflow, and acceptance. On every authorized creation or revision, seek the simplest complete route: reuse existing capabilities, remove unnecessary steps, merge duplicate rules, and retire obsolete instructions. Keep optional detail in linked references. Preserve required behavior, evidence, permissions, and failure handling; fewer words or steps alone do not prove an improvement.

Prefer existing local tools or small scripts for deterministic transformations, validation, file handling, and repeated operations. Keep judgment and meaningful choices in the Skill; executable mechanics belong to their code owner. Describe how to invoke the code, its inputs, outputs, and failure behavior instead of duplicating its algorithm as prose. Reuse a working implementation before adding helpers; a one-off adapter belongs in task scratch unless a demonstrated reusable need justifies maintaining it.

Keep per-run inputs, parameters, intermediate code, logs, receipts and changing execution state in the [external task directory](../workflow-skill/references/project-cache-artifact-policy.md), passed to stable tools as data. Durable project knowledge belongs in project memory; maintained source, configuration and requested deliverables retain their declared owners. Skill folders are not task notebooks or runtime output directories.

Ordinary task completion, a new result, or a one-off exception does not trigger a global/domain Skill update. Project AI-index maintenance is the scoped exception: automatically reconcile root guidance and the project index when established intent, ownership or structure changes. Other Skill revisions require an explicitly requested durable rule change or an authorized reusable defect repair. Make the narrow correction in its owner, remove superseded guidance and verify it. Do not add a global rule for each observed case or automatically reinstall or publish Skills after tasks.

Preserve unrelated edits, existing private history, and unrelated installed skills. Execute real checks of changed behavior in the active task and fix failures there. Ending runs useful memory alongside [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md); it cannot gate publication or repair code.

### Promote rules without multiplying owners

For an authorized cross-project audit, distinguish a reusable failure mechanism from a project-specific recipe. Use concrete evidence from distinct consumers, or an explicit global user preference, before promoting a rule. Keep product identifiers, gameplay values, provider configuration, dated incidents, and acceptance records in their project owners.

Extend the existing Skill or one focused reference before adding another global Skill. Code owns state, lifecycle, and side-effect contracts; Verify owns evidence and acceptance boundaries; Workflow owns orchestration, Git delivery, browser surfaces, and resource policy; Project Memory owns durable knowledge. Other entries and project instructions link to the owner and add only local constraints; retire copied global procedures when consolidating their owner. Source and installed copies are deployment states, not independent definitions; a project adapter is justified only by its actual domain contract.

Check the rule's executable consumer as well as its prose. Consolidation is incomplete when a helper, installer, validator, or test still enforces the superseded behavior. Preserve distinct compatibility tests, update existing cases by purpose, and verify the affected real operation before claiming a recurring bug is prevented.

## Install

Use the official user Skill directory, `~/.agents/skills`, as the single installation root. `CODEX_HOME` (default `~/.codex`) still owns Codex configuration, global `AGENTS.md`, and bundled system resources; it is not the user Skill root. Do not maintain a second user Skill copy or bridge under `CODEX_HOME/skills`. For an authorized migration, preserve unique content and recoverable backups, verify the destination, then retire the old user copies; preserve `.system` and plugin-managed resources.

When a task exposes an old Skill root, duplicate installation, or stale path in maintained code or instructions, automatically apply the [directory repair workflow](references/skill-directory-repair.md) within the task's scope. Correct the owning source and installed copy together. Project Skills stay in their declared project owner: visible `skills/` when selected, with existing `.agents/skills` projects supported. Never recreate a hidden duplicate after a visible-source migration. Use the local repair helper for file migration; report unresolved conflicts or permissions without guessing or bypassing controls. Do not rescan every project during ordinary tasks.

Use `scripts/sync_global_skills.py deploy --source-dir ROOT --skills-dir TARGET`. The installer materializes managed sources, locks the target, backs up recoverably, replaces exact managed targets, and restores on failure. It preserves user AGENTS files and unrelated skills. The CLI then runs Project Memory setup: it reuses the configured vault or creates one from `qin-llm-wiki`, prints the exact path and backup warning, and reports setup failure as pending without writing to Codex. Existing `task-analyze-skill/local/` files are legacy recovery inputs only. Installation performs recoverable replacement without running verification tasks or a release gate.

Only an explicit global AGENTS update uses `install-global-agents`; it creates a persistent backup with a restore command. Source changes, local installation, and remote publication are distinct outcomes.

Skills are selected on demand; installation alone does not make a Skill an always-run hook. For an explicitly authorized mandatory AI-index startup entry, use `install-global-agents --source-dir ROOT --startup-only`: it recoverably replaces only the marked startup block and preserves all other global guidance. Ordinary official-root deployment reports missing/stale activation or a shadowing global override without changing user instructions. Verify in a fresh Codex session; existing sessions may retain their original instruction chain.

On Windows, every managed installation inherits the destination Skill root's permissions for the new files before restoring private local state. This prevents private staging permissions from excluding the normal account. Permission failures stop installation and restore the previous targets; preserve private state, unrelated skills, and the destination root's access policy.

## Publish

Publish only when authorized. The script's `push` command validates the exact selected candidate and its isolated installation before maintained-source writes, staging, commit, or push. The catalog lists current behaviors and executable checks; retire obsolete workflow tests when the user changes those behaviors. Never invent attestation evidence.

Select each task-owned source file with a repeated `--include-path`; include generated README files when their templates change. Select already-local task commits explicitly with repeated `--include-commit` full hashes, including recovery after a failed delivery. The publisher uses the selected branch's existing configured upstream, integrates with merge, preserves unselected working files and index entries, and reads back that exact remote ref. Missing upstream or unresolved integration remains pending with its local commit and recovery state; `--repo` is not a substitute for the source branch's configured destination. Never pass a directory to include unrelated edits or authorize unknown ahead commits merely because they are present.

Keep source portable and free of private history, machine paths and secrets. After exact source, installation or release readback, remove disposable external support and intermediates under the [resource lifecycle](../workflow-skill/references/task-resource-lifecycle.md). Put requested deliverables or minimum recovery state in their actual owner first; preserve review/reuse files and environments until their references are safely rebound. Clean-clone release tests stay in each Skill's non-runtime `tests/`; remove duplicate or retired cases. Other harnesses follow the [test placement policy](../workflow-skill/references/project-cache-artifact-policy.md).

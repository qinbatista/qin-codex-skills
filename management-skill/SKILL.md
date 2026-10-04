---
name: management-skill
description: "Maintain, install, or publish managed global skills, and repair legacy user or project Skill directories and references when encountered."
---

# Skill Management

Before any file write, apply the [Cache policy](../workflow-skill/references/project-cache-artifact-policy.md). All temporary support belongs only in ignored `Cache/temp-*` or `Cache/tmp-*` from its first write. Inspect exact paths and the Git index before staging or committing; temporary files never enter Git. Source, installed updates, and retained recovery backups keep their declared owners.

Use for requested skill maintenance, installation, or publication. Ensure the Obsidian vault through Project Memory and read related project memory; skip absent matching records and isolate other projects. Briefly explain the intended steps before execution.

## Maintain

Each skill's source directory is its owner. Global skills describe reusable concepts and preferences; project skills own concrete domain implementations. Apply the authoring rules below when creating or updating either kind.

### Authoring rules

Keep Skills focused on stable rules, decision criteria, essential workflow, and acceptance. On every authorized creation or revision, seek the simplest complete route: reuse existing capabilities, remove unnecessary steps, merge duplicate rules, and retire obsolete instructions. Keep optional detail in linked references. Preserve required behavior, evidence, permissions, and failure handling; fewer words or steps alone do not prove an improvement.

Prefer existing local tools or small scripts for deterministic transformations, validation, file handling, and repeated operations. Keep judgment and meaningful choices in the Skill; executable mechanics belong to their code owner. Describe how to invoke the code, its inputs, outputs, and failure behavior instead of duplicating its algorithm as prose. Reuse a working implementation before adding helpers; a one-off adapter belongs in task scratch unless a demonstrated reusable need justifies maintaining it.

Keep per-run inputs, parameters, intermediate code, logs, receipts, and changing execution state in task-owned [Cache](../workflow-skill/references/project-cache-artifact-policy.md), passed to stable tools as data. Durable project knowledge belongs in project memory; maintained source, configuration, and requested deliverables retain their declared owners. Skill folders are not task notebooks or runtime output directories.

Ordinary task completion, a new result, or a one-off exception does not trigger a Skill update. Revise a Skill only for an explicitly requested durable rule change or an authorized repair to a demonstrated reusable instruction/tool defect. Make the narrow correction in its existing owner, remove superseded guidance, and verify that change. Do not add a global rule or mandatory step for every observed case, or automatically rewrite, reinstall, or publish Skills after each task.

Preserve unrelated edits, existing private history, and unrelated installed skills. Execute real checks of changed behavior in the active task and fix failures there. Ending only writes useful Obsidian memory; it cannot gate publication or repair work.

## Install

Use the official user Skill directory, `~/.agents/skills`, as the single installation root. `CODEX_HOME` (default `~/.codex`) still owns Codex configuration, global `AGENTS.md`, and bundled system resources; it is not the user Skill root. Do not maintain a second user Skill copy or bridge under `CODEX_HOME/skills`. For an authorized migration, preserve unique content and recoverable backups, verify the destination, then retire the old user copies; preserve `.system` and plugin-managed resources.

When a task exposes an old Skill root, duplicate installation, or stale path in maintained code or instructions, automatically apply the [directory repair workflow](references/skill-directory-repair.md) within the task's scope. Correct the owning source and installed copy together. Project Skills stay under that project's `.agents/skills`. Use the local repair helper for file migration; report unresolved conflicts or permissions without guessing or bypassing controls. Do not rescan every project during ordinary tasks.

Use `scripts/sync_global_skills.py deploy --source-dir ROOT --skills-dir TARGET`. The installer materializes managed sources, locks the target, backs up recoverably, replaces exact managed targets, and restores on failure. It preserves user AGENTS files and unrelated skills. The CLI then runs Project Memory setup: it reuses the configured vault or creates one from `qin-llm-wiki`, prints the exact path and backup warning, and reports setup failure as pending without writing to Codex. Existing `task-analyze-skill/local/` files are legacy recovery inputs only. Installation performs recoverable replacement without running verification tasks or a release gate.

Only an explicit global AGENTS update uses `install-global-agents`; it creates a persistent backup with a restore command. Source changes, local installation, and remote publication are distinct outcomes.

## Publish

Publish only when authorized. The script's `push` command runs the release gate before README generation, staging, commit, or remote mutation. The catalog lists current behaviors and executable checks; retire obsolete workflow tests when the user changes those behaviors. Never invent attestation evidence.

Keep source portable and free of private history, machine paths, and secrets. After exact source, installation, or release readback, remove task-owned `Cache/temp-*` and `Cache/tmp-*` support, disposable tests, and intermediates under the [resource lifecycle](../workflow-skill/references/task-resource-lifecycle.md). Put requested deliverables or minimum recovery state in their declared durable owner first; evidence or future review is not a temp-retention exception. Tests needed by a clean-clone release stay in each skill's non-runtime `tests/`; remove duplicate or retired cases instead of expanding the suite. Other test harnesses follow the [test placement policy](../workflow-skill/references/project-cache-artifact-policy.md).

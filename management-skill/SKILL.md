---
name: management-skill
description: "Automatically maintain project AI indexes and concise root guidance; maintain, install or publish global skills, and repair legacy Skill directories and references."
---

# Skill Management

Before writing, apply the [project Cache artifact policy](../workflow-skill/references/project-cache-artifact-policy.md). Keep scratch in the owning Cache from its first write, and source, installations and recovery backups with their owners. Check exact paths and the Git index before committing.

Briefly explain the intended steps. Resolve the vault through Project Memory and use only relevant, exact-project records when available.

## Maintain

Maintain each Skill in its source directory. Global Skills own reusable rules and preferences. Project Skills own concrete implementations.

### Automatic project AI index

At start/resume and finish, use [the project AI-index function](references/project-ai-index.md) for the current project. Update its index for every project change. Only an explicit change of main project selects a new project. Reference lookups skip prompts and maintenance. Pass `--project-scope reference` if invoking the helper there. Ask for consent before reading rules for and creating a first index. Repair or expand any existing index within editable scope without another creation question.

Use the project-local `skills/ai-index` owner by default. Migrate `.agents/skills/ai-index` safely within authorized scope unless the user selects another location. Keep it out of global installs and plugins. Use `scripts/project_ai_index.py` to validate routes and apply reviewed, source-bound changes.

When inspection or apply reports `compression.status: due`, run [AI Index Compression](references/project-ai-index.md#ai-index-compression) inline. Review flagged guidance and matching Obsidian scopes before edits and recheck before delivery.

For every local code edit, including tests, use [code navigation](references/project-ai-index.md#code-navigation) by module, exact file and reviewed method or key line, with scoped memory and necessary relationships. Keep stable targets current and selected excerpts bounded. Store history in Project Memory. Follow Code for method boundaries and extraction.

For the current editable project, read `cache/README.md` and optional `owners.json` at startup and finish. After native cleanup, run `project_ai_index.py cache --project-root ROOT --apply` to replace the bounded, ignored `cache/current.json` inventory with current entries only. `inspect` and `check` report stale state without writing. Reference and explicit read-only work skip writes.

### Authoring rules

Write every new or revised passage in English, including project documentation, Skills, `AGENTS.md`, AI-index prose and metadata, and [durable memory](../project-memory-skill/SKILL.md). This applies in any team, source, template or conversation language. Review before saving or delivering. Preserve exact identifiers, paths, commands and quotations where fidelity requires them.

Keep stable rules, decisions, essential steps and acceptance in the Skill. Reuse existing capabilities, merge duplicates and retire obsolete instructions. Put conditional detail in linked references. Check that shortening preserves routing, required behavior, evidence, permissions and failure handling.

Use existing local tools for deterministic transformations, validation, file handling and repeated operations. Describe invocation, inputs, outputs and failures in the Skill. Keep mechanics with their code owner and add helpers only for demonstrated reuse. Pass run inputs, adapters and changing state as data from the [project Cache task directory](../workflow-skill/references/project-cache-artifact-policy.md). Store durable knowledge in project memory and keep source, configuration and deliverables with their owners.

Revise global or domain Skills for explicitly requested durable changes or authorized reusable defect repairs. Keep corrections narrow and remove superseded rules. Maintain the current project's index after each project change and root guidance as needed. Installation and publication follow their own authorization.

Preserve unrelated edits, installed Skills and private history. Verify changed behavior and fix failures in the active task. Ending handles memory and [Workflow's resource audit](../workflow-skill/references/ending-resource-audit.md). Complete publication checks and code repair in the active task.

### Promote rules without multiplying owners

For authorized cross-project audits, promote a rule only with evidence from distinct consumers or an explicit global preference. Keep product identifiers, configuration values, provider settings, incidents and acceptance records with their project owners.

Extend an existing Skill or focused reference first. Code owns state, lifecycle and side effects. Verify owns acceptance evidence. Workflow owns coordination, Git, browser surfaces and resources. Project Memory owns durable knowledge. Link to the owner and add only local constraints. Remove copied procedures when consolidating. Keep one source definition across installations and add project adapters only for real domain contracts.

Check helpers, installers, validators and tests for superseded behavior. Update cases by purpose, preserve distinct compatibility coverage and verify the actual operation before claiming the fix prevents recurrence.

## Install

For a supported pack, use [install_skill_pack.py](scripts/install_skill_pack.py) with `install`, `update` or `uninstall` and the pack name. It reads the selected package from the repository's `master` archive, installs each Skill directly inside its group, and updates the whole group. Resolve helpers relative to the loaded Skill or its siblings.

Use `~/.agents/skills` for standalone user Skills. Resolve `CODEX_HOME` (default `~/.codex`) for configuration, global `AGENTS.md`, plugins and system resources. Preserve `.system`, plugin resources and unique content. Verify the destination before retiring an authorized legacy copy.

Apply the [directory repair workflow](references/skill-directory-repair.md) to encountered old roots, duplicates and stale paths within scope. Correct source and installation together using the repair helper. Keep project Skills in their single declared owner, visible `skills/` or existing `.agents/skills`. Report conflicts and permission failures. Limit discovery to affected owners.

For explicitly requested legacy loose-Skill installation, run `scripts/sync_global_skills.py deploy --source-dir ROOT --skills-dir TARGET` from the source checkout. It locks the target, backs up, replaces exact managed targets and restores on failure, preserving user AGENTS and unrelated Skills. It reports vault status via `--existing-only` and treats existing `task-analyze-skill/local/` as recovery inputs. The release gate applies to publication. Report source, installation and publication outcomes separately.

Use Workflow's `task_artifact_scope` for installer, candidate and regression runs, closing owned files and registration on success or failure. Preserve borrowed runs and bind release subprocesses to the candidate project's Cache. Isolate live probe profiles and output in their own registered owner. Report the exact cleanup failure path and reason alongside the original error or timeout.

Skills load on demand. Change always-loaded global guidance only on explicit request through `install-global-agents`, which keeps a persistent backup and restore command.

- For the mandatory AI-index startup entry, use `install-global-agents --source-dir ROOT --startup-only` to replace only the marked startup block. Verify in a fresh Codex session because existing sessions may retain prior instructions.
- For Ending/closeout repair, use `install-global-agents --source-dir ROOT --closeout-only` to replace the marked block or one recognized legacy Ending paragraph. Preserve unrelated guidance and memory routing. Stop on ambiguous markers or conflicting copies. Follow Project Memory's inline closure and keep chat lifecycle user-managed.

Ordinary official-root deployments report stale, missing or shadowed activation without changing user guidance. Report startup and closeout activation separately.

On Windows, inherit destination Skill root permissions before restoring private local state. On permission failure, stop and restore previous targets. Preserve private state, unrelated Skills and destination access policy.

## Publish

Publish only when authorized. The `push` command validates the exact candidate and isolated installation before maintained-source writes, staging, commit or push. Use the current capability catalog and real check results. Retire obsolete tests when the user changes the behavior they cover.

Select exact task files with repeated `--include-path`, including generated READMEs when templates change. Select known task commits, including recovery commits, with repeated `--include-commit` full hashes. Use the configured upstream and read back its exact remote ref. Fast-forward upstream-only changes and rebase only unpublished local commits with `--no-rebase-merges`. Preserve unselected work and index entries. Report missing upstream or unresolved integration with the local commit and recovery state.

Keep source portable and free of private history, machine paths and secrets. After readback, release disposable support under the [resource lifecycle](../workflow-skill/references/task-resource-lifecycle.md). Hand off final deliverables and minimum recovery state first, and preserve review/reuse resources until references are rebound. Keep clean-clone tests in each Skill's non-runtime `tests/`, retire duplicates and obsolete cases, and follow the [test placement policy](../workflow-skill/references/project-cache-artifact-policy.md) for other harnesses.

---
name: management-skill
description: "Maintain, install, or publish the managed global skills from their source repository."
---

# Skill Management

Use for requested skill maintenance, installation, or publication. Ensure the Obsidian vault through Project Memory and read related project memory; skip absent matching records and isolate other projects. Skill-governed maintenance keeps the user's selected model and effort unless the user bypasses skills for the maintenance task.

## Maintain

Each skill's source directory is its owner. Keep entry instructions concise, put distinct domain guidance in linked references, and remove obsolete rules when the workflow changes. Global skills describe reusable concepts and preferences; project skills own concrete domain implementations.

Preserve unrelated edits, Obsidian routing history, and unrelated installed skills. Execute real checks of changed behavior in the active task and fix failures there. Ending only writes useful Obsidian memory with the selected model; it cannot gate publication or repair work.

## Install

Use `scripts/sync_global_skills.py deploy --source-dir ROOT --skills-dir TARGET`. The installer materializes managed sources, locks the target, backs up recoverably, replaces exact managed targets, and restores on failure. It preserves user AGENTS files and unrelated skills. The CLI then runs Project Memory setup: it reuses the configured vault or creates one from `qin-llm-wiki`, prints the exact path and backup warning, and reports setup failure as pending without writing to Codex. Existing `task-analyze-skill/local/` files are legacy recovery inputs only; the active routing writer uses Obsidian. Installation does not run routing, benchmarks, verification tasks, or a release gate.

Only an explicit global AGENTS update uses `install-global-agents`; it creates a persistent backup with a restore command. Source changes, local installation, and remote publication are distinct outcomes.

## Publish

Publish only when authorized. The script's `push` command runs the release gate before README generation, staging, commit, or remote mutation. The catalog lists current behaviors and executable checks; retire obsolete workflow tests when the user changes those behaviors. Never invent attestation evidence.

Keep source portable and free of private history, machine paths, and secrets. Temporary support belongs in task-owned `Cache/temp-*` and is removed after release readback unless review or debugging still needs it. Tests needed by a clean-clone release stay in each skill's non-runtime `tests/`; remove duplicate or retired cases instead of expanding the suite. Other test harnesses follow the [test placement policy](../workflow-skill/references/project-cache-artifact-policy.md). Retained `Cache/remote-*` evidence requires a project use and reason and is preserved with sync destination pending until selected.

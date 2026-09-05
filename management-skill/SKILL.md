---
name: management-skill
description: "Maintain, install, or publish the managed global skills from their source repository."
---

# Skill Management

Use for requested skill maintenance, installation, or publication. Read related project memory if available; skip missing memory and isolate other projects. Skill-governed maintenance keeps the user's selected model and effort unless the user bypasses skills for the maintenance task.

## Maintain

Each skill's source directory is its owner. Keep entry instructions concise, put distinct domain guidance in linked references, and remove obsolete rules when the workflow changes. Global skills describe reusable concepts and preferences; project skills own concrete domain implementations.

Preserve unrelated edits, private routing history, and unrelated installed skills. Test changed behavior with focused cases in the active task. Ending only writes useful memory with the selected model.

## Install

Use `scripts/sync_global_skills.py deploy --source-dir ROOT --skills-dir TARGET`. The installer materializes managed sources, locks the target, backs up recoverably, replaces exact managed targets, and restores on failure. It preserves user AGENTS files, unrelated skills, and `task-analyze-skill/local/`. Installation does not run routing, benchmarks, verification tasks, or a release gate.

Only an explicit global AGENTS update uses `install-global-agents`; it creates a persistent backup with a restore command. Source changes, local installation, and remote publication are distinct outcomes.

## Publish

Publish only when authorized. The script's `push` command runs the release gate before README generation, staging, commit, or remote mutation. The catalog lists current behaviors and executable checks; retire obsolete workflow tests when the user changes those behaviors. Never invent attestation evidence.

Keep source portable and free of private history, machine paths, and secrets. Temporary support belongs in `Cache/tmp-*`; reusable tests stay with their skill.

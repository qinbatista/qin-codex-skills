# qin-codex-skills

## Scope and ownership

- This repository is the source for public Codex global Skills and lifecycle contracts.
- Each top-level Skill owns its `SKILL.md`, metadata, references, scripts, and focused tests.
- `management-skill` owns publication and runtime mirror deployment; do not treat a source edit as deployment.
- `task-analyze-skill` owns routing and receipts; `project-memory-skill` owns durable, sanitized project-change records.

## Stable entry points and constraints

- Route admitted work with `task-analyze-skill/scripts/obsidian_adaptive_model_runner.py`.
- Publish only through `management-skill/scripts/sync_global_skills.py` when authorized.
- Keep support artifacts under `Cache/`; never embed machine-specific paths, secrets, or task history in Skill source.
- Keep `AGENTS.md` structural: ownership, entry points, hard constraints, conventions, and definition of done only.

## Definition of done

- Preserve the owning Skill's scope and public contract, add focused regression coverage for durable behavior changes, and run the smallest relevant validation before handoff.

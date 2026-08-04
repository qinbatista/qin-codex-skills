# qin-codex-skills Knowledge

This repository is the source for the public Codex global Skills and their lifecycle contracts.

- Ownership: each top-level Skill owns its `SKILL.md`, agent metadata, references, scripts, and tests; `management-skill` owns publication and global deployment; `project-memory-skill` owns durable project/task records; `task-analyze-skill` owns routing, receipts, and model identity; `workflow-skill` owns execution lifecycle.
- Entrypoints: `task-analyze-skill/scripts/obsidian_adaptive_model_runner.py` routes admitted producer work; `management-skill/scripts/sync_global_skills.py` publishes and deploys the approved mirror; `project-memory-skill/scripts/project_change_memory.py` records project-scoped rationale.
- Routing memory: preserve project, task, module, file, symbol, capability, model, effort, failure, and verification context through native project-to-Model-Switch-to-category links; do not add a JSON routing sidecar.
- Deployment boundary: source changes are published from this repository, then mirrored into the runtime global Skills directory through the management entrypoint; generated README files and the global lifecycle contract are maintained by that entrypoint.
- Cache boundary: `Cache/cache_path.json` is untracked AI-only external-path registry state; disposable checks and receipts belong under `Cache/` and are not public source.

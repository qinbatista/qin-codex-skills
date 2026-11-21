# Repository and assets

The eight top-level Skill folders are the maintained public sources. Each owns its references, assets, executable helpers and non-runtime release tests. Project implementations and this index stay in project Skills. Keep public source free of private history, secrets, machine-specific paths and changing task evidence.

[Management](../../../management-skill/SKILL.md) owns authoring, directory repair, installation and publication. Use `management-skill/scripts/sync_global_skills.py` for managed delivery. Installation uses locking, recoverable backups and rollback; preserve unrelated Skills, private state and user AGENTS files. Install user Skills only in `~/.agents/skills`; project Skills stay in their declared visible `skills/` or existing `.agents/skills` owner. Resolve `CODEX_HOME` separately for configuration, global AGENTS and bundled resources. Repair encountered legacy roots through Management; do not create duplicate roots or directory bridges. Updating global AGENTS requires explicit authorization.

Start Skill source changes from the verified release source branch `master`. Apply Workflow's overlap check and isolate in a minimal local worktree when necessary. Land verified source changes on `master` through the release gate. Select exact task paths and reviewed commits, preserve unrelated edits and index entries, and verify normal remote delivery before closing a task worktree. Source delivery, installation and package publication use their own readbacks. [Workflow's Git contract](../../../workflow-skill/SKILL.md#git-branch-ownership)

For a Windows global Skill update, protect unrelated dirty work and pull current published source before Windows checks. Repair Windows defects in maintained source, verify both platforms, then publish and read back both checkouts and installations.

Before staging, inspect exact paths and the Git index. Temporary support never enters Git. Canonical runtime/assets, maintained tests and final deliverables retain their owners; project Cache task support follows [execution and resources](execution.md).

Track and commit stable project AI-index instructions, routes, metadata and Cache owner rules, including under `.agents/`. Keep dynamic inventories, temporary files, secrets and private data out of Git, and verify shared index updates on the configured upstream.

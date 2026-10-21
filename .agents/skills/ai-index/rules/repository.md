# Repository and assets

The eight top-level Skill folders are the maintained public sources. Each owns its references, assets, executable helpers and non-runtime release tests. Project implementations and this index stay in project Skills. Keep public source free of private history, secrets, machine-specific paths and changing task evidence.

[Management](../../../../management-skill/SKILL.md) owns authoring, directory repair, installation and publication. Use `management-skill/scripts/sync_global_skills.py` for managed delivery. Installation uses locking, recoverable backups and rollback; preserve unrelated Skills, private state and user AGENTS files. Install user Skills only in `~/.agents/skills`; project Skills stay in their project's `.agents/skills`. Resolve `CODEX_HOME` separately for configuration, global AGENTS and bundled resources. Repair encountered legacy roots through Management; do not create duplicate roots or directory bridges. Updating global AGENTS requires explicit authorization.

Follow [Workflow's Git ownership and delivery contract](../../../../workflow-skill/SKILL.md#git-branch-ownership). Inspect branch/upstream, index and dirty work; preserve unrelated changes. Publish only within the user's scope and after the release gate. Select exact task-owned paths and commits; never include unknown ahead commits, unrelated index entries or private data by inference. Source edits, installation and remote publication are separate outcomes with separate readbacks.

For a Windows global Skill update, protect unrelated dirty work and pull current published source before Windows checks. Repair Windows defects in maintained source, verify both platforms, then publish and read back both checkouts and installations.

Before staging, inspect exact paths and the Git index. Temporary support never enters Git. Canonical runtime/assets, maintained tests and final deliverables retain their owners; external task support follows [execution and resources](execution.md).

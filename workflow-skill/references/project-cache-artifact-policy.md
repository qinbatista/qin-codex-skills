# Project Cache Artifact Policy

Load this reference only when a task will create a Codex-selected support artifact or use a machine-specific external path. Durable requested source files and final deliverables stay in their declared source or output locations.

## Placement and retention

- Resolve the authoritative project root before the first project-support write. Put disposable evidence, receipts, logs, snapshots, generated media, comparisons, debug data, intermediate code, test results, and ordinary test scratch under `<project-root>/Cache/`.
- Use only `Cache/tmp-<name>/` for one-task disposable work, `Cache/<YYYYMMDD>/` for short reuse with a recorded reason and review point, and `Cache/remote-<name>/` or `Cache/remote-test/` for explicitly retained material. Reusable formal tests remain source tests.
- Do not create new top-level `tmp/`, `tests/`, or `work/` support folders, and never use `~/.codex/cache` or `~/.codex/tmp` for project artifacts. If a legacy top-level directory already exists, preserve its contents and move it only through an authorized, ownership-safe migration.
- `Cache/cache_path.json` is the reserved AI-only external-path registry, not a directory category. When `Cache/` is not already ignored, explicitly ignore this file.

## Portable paths and external resources

- This policy applies to every local-machine path written into a Skill, script, source file, configuration, documentation, or command, not only Cache paths. Use project-root-relative paths or discover the project root at runtime and join paths with native APIs. Never publish a user-specific POSIX home absolute path, Windows drive-letter absolute path, or slash assumption.
- An unavoidable machine-specific path needed only for AI access to a project-external file, directory, or application may exist only in `Cache/cache_path.json` using `{"schema_version": 1, "scope": "ai_only", "paths": {...}}`. Each stable entry records `path`, `kind` (`file|directory|application`), and a short `purpose`.
- Project source, runtime, tests, package scripts, build, CI, and shipped configuration must never read this registry. Do not store credentials, tokens, secrets, business data, or task transcripts in it, and never commit, mirror, publish, or copy its absolute values into source, documentation, commands, logs, receipts, or memory.
- Validate an explicitly supplied external path first. Otherwise validate the registry schema, declared kind, existence, and readability before use. If one entry is missing or stale, perform one bounded platform-aware discovery, update only that key, and replace the registry atomically while preserving unrelated keys. Obsidian resolution may then use the project-specific order declared by its owning memory workflow, including `CODEX_OBSIDIAN_VAULT` and the configured open vault in `obsidian.json`; no workflow may invent a default machine path.

## Project structure and cleanup

- Project-root `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to owning documentation. Do not put implementation details, task history, logs, receipts, test results, generated data, long command blocks, or troubleshooting prose there.
- Reusable, retained, workflow-required, or project-influencing Cache content gets one concise `AGENTS.md` registry entry containing its exact Cache-relative path, structural role, owner/source of truth, and retention/version-control status. Link to the owning source, project documentation, or a README for details. Update `AGENTS.md` only when structure, ownership, a critical entry point, or a hard constraint changes.
- Before acquiring or releasing a task-created path, runtime, application, or browser resource, apply [Task Resource Lifecycle](task-resource-lifecycle.md). Release only exact resources owned by the current task after durable-result and last-consumer readback; retain or defer preexisting, shared, conflicted, Unity, date, and remote resources. Never use cleanup to control another Codex task, thread, session, or Ending.
- Final reports go only to the user-requested output location. Important retained Cache content is never deleted without explicit authorization.

# Project Cache Artifact Policy

Load this reference only when a task will create a Codex-selected support artifact or use a machine-specific external path. Durable requested source files and final deliverables stay in their declared source or output locations.

## Placement and retention

- Resolve the authoritative project root before the first project-support write. Put disposable evidence, receipts, logs, snapshots, generated media, comparisons, debug data, intermediate code, test results, and ordinary test scratch under `<project-root>/Cache/`.
- Use only `Cache/temp-<name>/` for disposable, test, uncertain, or intermediate work. Use `Cache/remote-<name>/` only when the user or project contract explicitly requires retention. Move explicitly retained work out of `temp-*` and update every reference to its new relative path. Reusable formal tests remain source tests.
- Do not create new top-level `tmp/`, `tests/`, or `work/` support folders, and never use `~/.codex/cache` or `~/.codex/tmp` for project artifacts. If a legacy top-level directory already exists, preserve its contents and move it only through an authorized, ownership-safe migration.
- Keep `Cache/` ignored. A private AI-only external-path registry, when needed, belongs under `Cache/remote-ai-paths/registry.json`.

## Portable paths and external resources

- This policy applies to every local-machine path written into a Skill, script, source file, configuration, documentation, or command, not only Cache paths. Use project-root-relative paths or discover the project root at runtime and join paths with native APIs. Never publish a user-specific POSIX home absolute path, Windows drive-letter absolute path, or slash assumption.
- An AI-only external-path registry uses `{"schema_version": 2, "scope": "ai_only", "paths": {...}}`. Each entry records a `base` (`home` or `project`), a relative `path`, `kind` (`file|directory|application`), and a short `purpose`. Resolve the base at runtime. Never write an absolute path into code or configuration.
- Project source, runtime, tests, package scripts, build, CI, and shipped configuration must never read this registry. The project-memory skill may read it only for AI memory access. Do not store credentials, tokens, secrets, business data, or task transcripts in it; never commit, mirror, or publish it.
- Validate an explicitly supplied external path first. Otherwise validate the registry schema, base, relative path, declared kind, existence, and readability before use. If one entry is missing or stale, perform one bounded platform-aware discovery, update only that key, and replace the registry atomically while preserving unrelated keys. Obsidian resolution may then use `CODEX_OBSIDIAN_VAULT` and the configured open vault in `obsidian.json`; no workflow may invent a default machine path.

## Project structure and cleanup

- Project-root `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to owning documentation. Do not put implementation details, task history, logs, receipts, test results, generated data, long command blocks, or troubleshooting prose there.
- Reusable, retained, workflow-required, or project-influencing Cache content gets one concise `AGENTS.md` registry entry containing its exact Cache-relative path, structural role, owner/source of truth, and retention/version-control status. Link to the owning source, project documentation, or a README for details. Update `AGENTS.md` only when structure, ownership, a critical entry point, or a hard constraint changes.
- Before acquiring or releasing a task-created path, runtime, application, or browser resource, apply [Task Resource Lifecycle](task-resource-lifecycle.md). Release only exact resources owned by the current task after durable-result and last-consumer readback; retain or defer preexisting, shared, conflicted, Unity, and remote resources. Never use cleanup to control another Codex task, thread, session, or Ending.
- Final reports go only to the user-requested output location. Important retained Cache content is never deleted without explicit authorization.

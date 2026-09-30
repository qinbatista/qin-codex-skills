# Repair legacy Skill directories

Apply when installing or maintaining Skills, or when an active task encounters a legacy directory or reference. The standing workflow authorizes routine repair within that task; explain the intended change and proceed without another confirmation. A request to audit all projects expands the scan to the user's available project roots. Report which projects were inspected, changed, already correct, or inaccessible.

## Identify the owner

- User Skills belong in `~/.agents/skills`; resolve the native home directory independently of `CODEX_HOME`.
- Project Skills belong in `PROJECT/.agents/skills`. Preserve project scope; never promote them to the user's global directory during migration.
- Codex configuration, global `AGENTS.md`, built-in `.system` resources, and plugin-managed resources retain their own locations. Legacy read-only history, isolated test fixtures, and deliberately frozen snapshots are not active installation defaults.

Read project instructions and existing changes before editing. Search maintained installers, path resolvers, wrappers, manifests, executable examples, and instructions for `.codex/skills`, `CODEX_HOME/skills`, and paths assembled from a Codex home variable. Inspect each use instead of replacing every `.codex` string. Avoid generated caches, dependencies, private memory, and historical evidence.

## Repair source and installation

Change confirmed user defaults to `Path.home() / ".agents" / "skills"` or the platform's equivalent. Keep configuration paths separate. Update project-relative consumers, manifests and required content hashes when moving a project Skill. If an older external installer has a destination option, pass the official target rather than editing bundled vendor code. Retire duplicate-copy and directory-bridge logic.

Use `scripts/repair_user_skill_root.py` for migration. Run `python3 -B scripts/repair_user_skill_root.py audit` for a read-only check, or use `apply` for recoverable repair. Add `--project-root PROJECT` for a project migration; use `py -3 -B` on Windows. Default managed installation invokes the same helper after the authoritative source is installed; an arbitrary explicit installation target must not mutate the real user's legacy directory.

The helper compares complete contents, preserves backups outside Skill discovery roots, verifies copied bytes, and only then retires a verified legacy directory. Missing targets and identical duplicates can be repaired automatically. Different contents require an identified authoritative source; otherwise preserve both and report the conflict. Preserve user AGENTS and private data in the recoverable backup. Do not follow links outside the declared roots, rewrite ACLs, change principals, or silently discard unreadable contents. A permissions failure remains pending.

For obsolete managed copies, pass `--source-dir REPOSITORY` only after the official installation is known to match that maintained source. The helper rechecks this match before retirement. Use `--backup-root PATH` to choose another recovery location outside both Skill roots. Pending results retain recovery paths. The standalone helper returns exit code 2 for pending repairs; a successful installation reports its separate repair status. Fix the stated condition before retrying.

Verify the actual new installation or project entry point, required manifest references, and the absence of active legacy copies. Check default target selection with an isolated home, including a separate `CODEX_HOME`; a string search alone is insufficient for executable path changes. Re-running repair should leave an already-correct installation unchanged. Report source, installed, retired, pending, and publication status separately.

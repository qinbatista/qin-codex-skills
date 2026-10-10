# External Task Artifact Policy

Read this reference before any task-selected file write, including browser evidence, helper/test output, and delegated work. Classify the file by its purpose before choosing its path. Maintained source/configuration and explicitly requested final deliverables keep their declared owners; a screenshot, JSON receipt, log, probe, or recovery observation does not become source merely because it is useful evidence.

## Resolve before the first write

All AI task support belongs outside every project directory and Codex-managed storage from its first write. This includes screenshots, JSON receipts, logs, probes, snapshots, generated candidates, comparisons, one-off code, test fixtures/results, tool caches and duplicate downloads. Ignoring a path in Git does not make project-local scratch acceptable. Never use project `Cache/temp-*`, root `output/`, `Outputs/`, `tmp/` or `work/` for these files.

Use `workflow-skill/scripts/task_artifact_paths.py` to resolve the external base, exact project identity and task ID. `resolve_task_artifact_root(project_root, task_id, create=True)` returns the isolated task directory; `task_artifact_environment(task_root, create=True)` binds child `TMP`, `TEMP` and `TMPDIR` to its `tmp` directory. Resolve paths with native APIs, share the same resolved owner with delegates, and assign separate branch subdirectories when writers run in parallel.

| Selection | External base |
| --- | --- |
| Explicit configuration | `YOFA_TASK_ARTIFACT_ROOT`, validated outside projects and Codex storage |
| Windows default | Discovered home joined with `YoFaAI/TaskArtifacts` |
| macOS default | Discovered home joined with `Library/Application Support/YoFaAI/TaskArtifacts` |
| Linux default | Discovered `XDG_CACHE_HOME`, or home `.cache`, joined with `YoFaAI/TaskArtifacts` |

Projectless work uses the same external resolver with its exact workspace/task identity. Missing, invalid or unavailable ownership/root resolution blocks the affected write; do not fall back to system Temp, Desktop, Downloads, a source folder or Codex session/visualization storage. Validate actual resolved storage, including packaged-app redirection: an apparently external environment path inside a Codex package/runtime cache is forbidden. Never hardcode a user's home, drive or account name. Reject links/reparse points that escape the resolved boundary.

Configure each tool's output, working directory and cache options before launch, together with the child temporary environment. Use `tempfile` only with an explicit directory inside that external task root. Disable project-local bytecode, pytest, coverage and equivalent test caches or bind them externally. Capture output in the current tool session when no file is needed. A tool that cannot honor this boundary leaves that check pending; it does not authorize writing scratch into the project.

## Preserve real owners

- Maintained source/configuration, versioned non-runtime tests and requested final deliverables keep their declared owners. Required native runtime/build caches, canonical asset originals/history, project services and their real resource/recovery Cache owners are not ordinary AI scratch. Do not blanket move a project's Cache or reclassify task evidence as a runtime resource merely to retain it.
- Keep changing run inputs, parameters, execution state and one-off adapters in the external task directory; pass them as data to stable tools. Durable project knowledge stays only in the configured Obsidian vault. Skill folders and project `AGENTS.md` hold stable instructions, not run inventories or task logs.
- Image generation still follows the [image workflow](image-generation.md). Bind native downloads to the exact job and SHA, move unchanged accepted files into their actual asset/deliverable owner, then release external staging and transport duplicates after the required acceptance/sync readback. Set download paths externally where the tool supports it; an unavoidable tool-owned staging copy is transferred and cleaned promptly, never adopted as permanent Downloads storage.
- A retained review/test environment or nonshipping harness needs an explicit external resource owner and working consumer references. Final assets and packages belong in their final owner. Renaming scratch to `remote-*`, or putting metadata beside it, does not establish retention or remote synchronization.
- Before cleanup, verify final bytes and consuming references through a fresh reader. On pause/failure, preserve minimum recovery inputs/state in the declared recovery owner and remove independent disposable support. Keep active, shared, user-opened and useful review/reuse resources until their owners and references are verified; missing metadata never authorizes deletion.

## Migrate existing misplaced scratch

Select exact paths through creation history, file identity and current consumer checks. Preserve canonical resources, source, maintained tests, final deliverables, unrelated work and uncertain files. Stop only confirmed owned disposable activity before moving its backing files. Move authorized legacy scratch to its isolated external owner, preserve bytes/hashes, update every affected consumer/reference and verify with a fresh reader before retiring the old location.

A migration is a separately authorized retention/move action, never a way to bypass a rejected deletion or other permission control. A rejected operation remains pending unless that control changes; report the exact target and reason. Do not infer migration authorization from a cleanup failure, broadly sweep project directories, or hide pending resources under a new name.

## Before staging and committing

Review the exact task path list, `git ls-files` and `git diff --cached --name-status`. Stage only maintained source/configuration and requested versioned deliverables. Temporary files never enter Git, regardless of filename or extension. Preserve unrelated index entries; use scoped paths rather than broad staging. Check for newly created project-local support/caches and remove only verified task-owned leftovers through their owner. Keep actual project runtime Cache ignored under its existing contract.

## Test file placement

- When project logic or goals change, inventory existing test files and their runner references. Remove obsolete and duplicate cases; revise a useful existing case before adding another file. Keep only tests that exercise a current behavior or a deliberate compatibility boundary.
- Put a nonshipping retained harness/fixture in its declared external resource owner. Tests required by source or a clean-clone release use the toolchain's versioned, non-runtime development area, such as a Skill's `tests/` or an appropriate Unity editor-only area; their run output and caches still stay external. Keep tests out of runtime source and final deliverable folders.
- After moving or removing a test, update runner commands, imports, fixture paths, documentation, and release checks, then execute the affected test from its final location. Do not keep a stale copy at the old path.

## Portable paths and external resources

- This policy applies to every local-machine path in Skills, scripts, source, configuration, documentation and commands. Discover external/task roots at runtime; use project-relative paths only for actual project-owned source/resources. Never publish a user-specific home/drive absolute path or slash assumption.
- An AI-only external-path registry uses `{"schema_version": 2, "scope": "ai_only", "paths": {...}}`. Each entry records a `base` (`home` or `project`), a relative `path`, `kind` (`file|directory|application`), and a short `purpose`. Resolve the base at runtime. Never write an absolute path into code or configuration.
- Project source, runtime, tests, package scripts, build, CI, and shipped configuration must never read this registry. Memory Skills must never read or write it. Do not store credentials, tokens, secrets, business data, task transcripts, or memory locations in it; never commit, mirror, or publish it.
- Keep this private non-memory registry in a declared external AI resource owner, never project Cache or Codex storage. Validate an explicitly supplied external test fixture path first. Otherwise validate the registry schema, base, relative path, declared kind, existence and readability before use. If one entry is missing/stale, perform one bounded platform-aware discovery, update only that key, and replace atomically while preserving unrelated keys. Obsidian memory resolution remains with Project Memory.

## Project structure and cleanup

- Project-root `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to owning documentation. Do not put implementation details, task history, logs, receipts, test results, generated data, long command blocks, or troubleshooting prose there.
- For a real retained/shared project Cache owner, keep one concise structural `AGENTS.md` pointer to its stable boundary and owning documentation. Keep changing run state and inventories with the actual resource owner. External scratch needs no project registry entry; update instructions only when a stable rule or ownership boundary changes.
- Before acquiring or releasing a task-created path, runtime, application, or browser resource, apply [Task Resource Lifecycle](task-resource-lifecycle.md). Clean exact task-owned disposable resources after verified durable delivery or minimum recovery handoff. Bounds-check resolved targets and use one native platform shell or the portable helper; do not traverse symlinks/reparse points. Preserve unrelated, preexisting, shared, active, review/reuse and Unity-owned resources. Ending's [bounded resource audit](ending-resource-audit.md) checks confirmed leftovers from completed chats after applying their owners' cleanup first. Report concrete ownership/identity conflicts rather than claiming cleanup completed. Never use cleanup to control another Codex task, thread, session, or Ending, or purge Codex-managed storage.
- Final reports go only to the user-requested output location. Important retained resources are never deleted without explicit authorization. This policy supersedes earlier global project-Cache scratch placement; it does not relocate canonical runtime/assets or overwrite user `AGENTS.md` files during deployment.

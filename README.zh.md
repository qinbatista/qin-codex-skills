# qin-codex-skills

This repository maintains eight reusable global Codex Skills for task analysis, code and prompt authoring, verification, project memory, installation, and publication. The Skills make work consistent and verifiable across projects. Each project owns its domain rules.

Preview the objective and the implementation steps before starting. The user can steer or stop the work at any time. Pause only for necessary information or authorization.

## Skill responsibilities

| Skill | Responsibility |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Tracks Skill use, clarifies the objective, requires delivery, and recovers from failures. |
| [Workflow](workflow-skill/SKILL.md) | Coordinates work and resource cleanup while preserving active resources and review or reuse inputs. |
| [Code](code-skill/SKILL.md) | Guides code structure, clear implementation, and portable, quiet execution. |
| [Prompt](prompt-skill/SKILL.md) | Defines inputs, constraints, and output contracts for reusable prompts. |
| [Verify](verify-skill/SKILL.md) | Checks actual behavior or output in the active task and focuses test coverage. |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls relevant project context and records useful durable changes in Obsidian. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Installs managed Skills recoverably and verifies authorized publication. |

## Task flow

1. At startup or resume, [check the current project's AI index](management-skill/references/project-ai-index.md). If it is missing, obtain first-bootstrap consent before reading rules or creating it. Ask again at the next startup if it remains absent. Reference lookups leave the current project unchanged and trigger no index prompt or maintenance. Reuse focused module rules in an existing index, ensure the Obsidian vault is available, recall scoped project facts, skip absent matching memory, and track actual Skill use.
2. Preview the objective and steps, then execute. Report material changes to the approach as they occur.
3. Update concise root `AGENTS.md` and the project AI index when accepted intent or structure changes and before delivery. Read the project testing Skill before adding a maintained test. Verify the real affected case, fix failures, and release disposable resources.
4. Close out guidance, memory, and resources in the active task under [Project Memory](project-memory-skill/SKILL.md) and [Workflow](workflow-skill/SKILL.md). Preserve active resources and resources needed for review or reuse.

Use progress updates for material developments. At completion, report the exact Skills used, what they did, and why, including branch work. Identify unused, missing, or unreadable Skills separately. Follow the [mandatory reporting rules](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting).

Project memory lives in each project's `Memory.json` with a readable `Knowledge.md` view. Recall by exact project, module, file, and method. Exclude stale entries from current context. Consolidate touched entries, maintain due project synthesis, and keep references explicit. Each project owns its own memory, and shared preferences are selected only when relevant.

The global workflow checks the current project's local index at startup, on applicable changes, and at finish. Each project retains its own index. The helper validates routes and applies reviewed changes against source evidence and file hashes. Index maintenance is part of task execution, and reviewed rules determine the index structure.

[AI Index Compression](management-skill/references/project-ai-index.md#ai-index-compression) identifies oversized guidance at checkpoints, compares it with source and scoped Obsidian knowledge, and preserves effective rules and history.

For local code changes, including tests, locate the module, file, method or key-line anchor, and necessary relationships. Recall exact-scope memory and verify current source. Keep stable responsibilities and entry points in the index. Selected routes return bounded source excerpts. Keep related behavior cohesive, parameterize variants when appropriate, and refresh routes touched by a change.

Write project documentation, Skills, `AGENTS.md`, AI-index guidance, and durable memory in English. Follow [Management's authoring rules](management-skill/SKILL.md#authoring-rules).

## Source and installation

Install user Skills in `~/.agents/skills`, the [official Codex location](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills). `CODEX_HOME` defaults to `~/.codex` and owns configuration, global `AGENTS.md`, and bundled resources. Apply [the directory repair workflow](management-skill/references/skill-directory-repair.md) to legacy paths. Keep project Skills in their projects and preserve `.system`, plugins, and recoverable backups.

Skill directories contain instructions, references, helpers, and versioned release tests. Put temporary support, screenshots, receipts, test output, and tool caches in a fresh ignored `Cache/temp-<task>/` from the first write, following [the project Cache artifact policy](workflow-skill/references/project-cache-artifact-policy.md). Use the current workspace Cache for projectless work. Verify any inputs carried into a new run. After verifying delivery or handing off minimum recovery inputs, release disposable support and preserve source, assets, and resources needed for review or reuse. Verify ownership and active consumption of any `remote-*` resource before retaining it.

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

Use `py -3 -B` on Windows. Installation uses locking, backup, and recovery to update the eight managed Skills while preserving unrelated Skills, user AGENTS files, and private history. The memory check uses `--existing-only` and leaves an absent vault pending. First-vault creation requires separate authorization. An explicit `install-global-agents --source-dir .` creates a restorable backup before updating global AGENTS.

The mandatory AI-index startup gate runs through global instructions. After authorization, use `install-global-agents --source-dir . --startup-only` to update the startup block and preserve personal rules. Normal deployment reports a missing, stale, or shadowed entry. Verify activation in a fresh Codex session.

Source edits, installation, and GitHub publication are distinct. Pass `--include-path` to `push` for each task-owned file and `--include-commit` with the full hash for each authorized existing local commit. The publisher integrates, verifies, pushes normally, and reads back the configured upstream while preserving unselected worktree and index changes.

## Code reference owners

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [State, async results and side effects](code-skill/references/state-and-side-effects.md)
- [Actual target and evidence boundaries](verify-skill/SKILL.md#bind-evidence-to-the-actual-target)
- [Python](code-skill/references/python-rules.md)
- [Unity C#](code-skill/references/unity-csharp-rules.md)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

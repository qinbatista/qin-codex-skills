# qin-codex-skills

This repository maintains eight global Codex skills. Projects retain domain rules.

## What each skill does

| Skill | Responsibility |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Reports Skill use; requires delivery and recovery. |
| [Workflow](workflow-skill/SKILL.md) | Coordinates work and cleanup; preserves active/review/reuse resources. |
| [Code](code-skill/SKILL.md) | Guides structure, readable code, and portable, quiet execution. |
| [Prompt](prompt-skill/SKILL.md) | Shapes reusable prompts with clear inputs, constraints, and output contracts. |
| [Verify](verify-skill/SKILL.md) | Checks real behavior in the active task; focuses test coverage. |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls project context and stores durable knowledge in Obsidian. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Maintains project indexes, installs skills recoverably and validates authorized publication. |

## Task flow

1. At startup/resume, [inspect or build the project AI index](management-skill/references/project-ai-index.md), then read relevant routes and exact-project memory. Ensure the Obsidian vault, skip missing memory, and track Skill use.
2. Preview the objective and implementation steps, then execute. Ask only for necessary decisions or authorization.
3. Update concise root `AGENTS.md` and `.agents/skills/ai-index` automatically when accepted intent or structure changes and before delivery. Consult project testing Skills; run real affected-case checks and clean disposable resources.
4. Before creating an unpinned projectless Ending, check native deletion; otherwise close out inline. Show its link and finish without waiting. Ending reconciles the index, consolidates memory, [cleans resources](workflow-skill/references/ending-resource-audit.md), and deletes itself. Preserve active/review resources; archival is not deletion.

At completion, summarize actual Skill names, steps and reasons once, including branch use; distinguish unused, missing or unreadable Skills. Progress updates need no repeated lists; [reporting is mandatory](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting).

One Memory.json and Knowledge.md serve each project. Recall excludes stale facts; Ending consolidates touched entries and links.

Project memories stay isolated. Read relevant shared preferences only. `AGENTS.md` and Skills own stable rules; changing facts and history live in Obsidian.

Each project owns its AI index, without global or plugin copies. The helper validates routes and applies reviewed updates against source and document hashes. This runs within the task workflow, not as a background watcher.

Without a vault, [Project Memory](project-memory-skill/SKILL.md) creates and verifies one outside Codex and the project using [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki). Back up the entire vault regularly: it holds all Codex and project memory. The generator is a public template, not a private-memory backup.

macOS/Linux: `python3 -B project-memory-skill/scripts/obsidian_vault_setup.py --project-root .`

Windows PowerShell: `py -3 -B project-memory-skill\scripts\obsidian_vault_setup.py --project-root .`

## Source and installation

Install user Skills only in `~/.agents/skills` ([official location](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)). `CODEX_HOME` (default `~/.codex`) owns configuration, global `AGENTS.md`, and system resources. Automatically [repair legacy roots](management-skill/references/skill-directory-repair.md); preserve `.system` and plugins.

Skills own instructions, helpers and release tests. Keep support in a fresh external `YoFaAI/TaskArtifacts/temp-*` run under [the artifact policy](workflow-skill/references/project-cache-artifact-policy.md). Verify selected continuation inputs, then release disposable directories and worktrees. Preserve source, deliverables, assets and active/review/reuse resources.

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

On Windows, use `py -3 -B` with the same Python entry point. Installation replaces the eight managed skills with locking, backup, and recovery, then ensures and reports the Obsidian memory vault. It preserves unrelated skills, user AGENTS, and existing private history. An explicitly requested global AGENTS update uses `install-global-agents --source-dir .` and creates a restorable backup.

Source, installation and GitHub publication are distinct. `push` selects task-owned files with `--include-path` and existing task commits with `--include-commit` full hashes. It merges, validates, pushes and reads back the configured upstream, preserving unselected worktree and index changes.

## Code reference owners

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [State, async results and side effects](code-skill/references/state-and-side-effects.md)
- [Actual target and evidence boundaries](verify-skill/SKILL.md#bind-evidence-to-the-actual-target)
- [Python](code-skill/references/python-rules.md)
- [Unity C#](code-skill/references/unity-csharp-rules.md)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

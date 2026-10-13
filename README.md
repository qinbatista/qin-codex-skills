# qin-codex-skills

This repository maintains eight global Codex skills. Projects retain domain rules.

## What each skill does

| Skill | Responsibility |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Tracks Skill use for a final summary; requires action delivery and recovery. |
| [Workflow](workflow-skill/SKILL.md) | Coordinates work and resource cleanup; preserves active use and user review/reuse. |
| [Code](code-skill/SKILL.md) | Guides structure, readable code, and portable, quiet execution. |
| [Prompt](prompt-skill/SKILL.md) | Shapes reusable prompts with clear inputs, constraints, and output contracts. |
| [Verify](verify-skill/SKILL.md) | Checks real behavior or outputs in the active task and keeps test coverage focused. |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls relevant project context and records useful durable changes in Obsidian. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Installs the managed skills recoverably and validates authorized publication. |

## Task flow

1. At startup or resume, ensure the Obsidian vault, then read applicable skills and exact-project memory. Track Skill use, steps and reasons; skip missing memory.
2. Preview the objective and implementation steps, then execute. Ask only for necessary decisions or authorization.
3. Before adding maintained tests, consult project testing Skills and consolidate duplicate purposes. Default to real affected-case checks; deliver evidence, repair failures and clean disposable resources.
4. Launch one authorized, unpinned projectless Ending, show its acknowledged link and immediately finish the main turn. The parent never waits for Ending. Ending reads its source chat when needed, records Obsidian memory and [audits resources](workflow-skill/references/ending-resource-audit.md) in parallel, and owns recovery and mandatory native self-deletion. Preserve active work and user review/reuse; archival remains deletion pending.

At completion, summarize actual Skill names, steps and reasons once, including branch use; distinguish unused, missing or unreadable Skills. Progress updates need no repeated lists; [reporting is mandatory](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting).

One Memory.json and Knowledge.md serve each project. Recall excludes stale facts; Ending consolidates touched entries and links.

Project memories stay isolated. Read relevant shared preferences only. `AGENTS.md` and Skills own stable rules; changing facts and history live in Obsidian.

Without a vault, [Project Memory](project-memory-skill/SKILL.md) creates and verifies one outside Codex and the project using [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki). Default: `~/Documents/Obsidian/LLM Memory`; override with `CODEX_OBSIDIAN_VAULT` or `--vault`. Back up the entire vault regularly: it holds all Codex and project memory. The generator is a public template, not a private-memory backup.

macOS/Linux: `python3 -B project-memory-skill/scripts/obsidian_vault_setup.py --project-root .`

Windows PowerShell: `py -3 -B project-memory-skill\scripts\obsidian_vault_setup.py --project-root .`

## Source and installation

Install user Skills only in `~/.agents/skills` ([official location](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)). `CODEX_HOME` (default `~/.codex`) owns configuration, global `AGENTS.md`, and system resources. Automatically [repair legacy roots](management-skill/references/skill-directory-repair.md); preserve `.system` and plugins.

Skills own instructions, helpers and release tests. The [external artifact policy](workflow-skill/references/project-cache-artifact-policy.md) places AI support outside projects and Codex under `YoFaAI/TaskArtifacts`. Each execution gets a fresh `temp-*`: request, test, build, package or deployment. Copy selected continuation inputs, verify bytes, then release completed directories and disposable worktrees. Preserve source, deliverables, canonical assets and active/review/reuse resources.

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

# qin-codex-skills

This repository maintains eight reusable global Codex skills. Projects retain their own domain rules.

## What each skill does

| Skill | Responsibility |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Reports Skill use throughout work; requires action delivery and recovery. |
| [Workflow](workflow-skill/SKILL.md) | Coordinates work and global resource cleanup, preserving active use and user review/reuse. |
| [Code](code-skill/SKILL.md) | Guides code structure, readable implementation, and portable, quiet execution. |
| [Prompt](prompt-skill/SKILL.md) | Shapes reusable prompts with clear inputs, constraints, and output contracts. |
| [Verify](verify-skill/SKILL.md) | Checks real behavior or outputs in the active task and keeps test coverage focused. |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls relevant project context and records useful durable changes in Obsidian. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Installs the managed skills recoverably and validates authorized publication. |

## Task flow

1. At startup or resume, show planned Skill names and purposes before tools. Ensure the Obsidian vault, then read applicable skills and exact-project memory. Missing memory is skipped.
2. Briefly describe the objective and implementation steps, then proceed. Do not add a confirmation checkpoint unless a necessary decision or authorization is missing.
3. Deliver requested work with a real behavior check inside the active task. Repair failures; separate changes from evidenced blockers. Update tests; clean disposable resources.
4. One authorized, unpinned projectless Ending records Obsidian memory and [audits resources](workflow-skill/references/ending-resource-audit.md) in parallel. Follow owners’ cleanup first; release disposable completed-task resources and preserve active work and user review/reuse. Unavailable memory stays pending; Ending never gates, tests or repairs the result.

Every progress update and phase transition repeats Skill names and purposes, including branches. Announce new selections before use; distinguish planned and applied Skills. Finals list actual use and purposes. Report none, missing or unused honestly; [reporting is mandatory](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting).

One Memory.json and Knowledge.md serve each project. Recall excludes stale facts; Ending consolidates touched entries and links.

Project memories stay isolated. Read relevant shared preferences only. `AGENTS.md` and Skills own stable rules; changing facts and history live in Obsidian.

Without a vault, [Project Memory](project-memory-skill/SKILL.md) creates and verifies one outside Codex and the project using [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki). Default: `~/Documents/Obsidian/LLM Memory`; override with `CODEX_OBSIDIAN_VAULT` or `--vault`. Back up the entire vault regularly: it holds all Codex and project memory. The generator is a public template, not a private-memory backup.

macOS/Linux: `python3 -B project-memory-skill/scripts/obsidian_vault_setup.py --project-root .`

Windows PowerShell: `py -3 -B project-memory-skill\scripts\obsidian_vault_setup.py --project-root .`

## Source and installation

Install user Skills only in `~/.agents/skills` ([official location](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)). `CODEX_HOME` (default `~/.codex`) owns configuration, global `AGENTS.md`, and system resources. Automatically [repair legacy roots](management-skill/references/skill-directory-repair.md); preserve `.system` and plugins.

Skills own instructions, references, helpers and release tests. Temporary screenshots, JSON receipts and test output use ignored `Cache/temp-<task>/` from the first write, never Git. Projectless work uses its workspace Cache. Delete disposable scratch after verified delivery or recovery handoff; preserve review/reuse files and backing resources until ownership and references are verified. A `remote-*` name alone does not establish retention.

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

On Windows, use `py -3 -B` with the same Python entry point. Installation replaces the eight managed skills with locking, backup, and recovery, then ensures and reports the Obsidian memory vault. It preserves unrelated skills, user AGENTS, and existing private history. An explicitly requested global AGENTS update uses `install-global-agents --source-dir .` and creates a restorable backup.

Source, installation and GitHub publication are distinct. `push` runs the release gate before staging or remote writes.

## Code reference owners

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [Python](code-skill/references/python-rules.md)
- [Unity C#](code-skill/references/unity-csharp-rules.md)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

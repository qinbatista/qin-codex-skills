# qin-codex-skills

This repository maintains eight reusable global Codex skills. Projects retain their own domain rules.

Briefly explain the outcome and implementation steps before execution, then proceed. Keep the user informed so they can redirect or interrupt.

## What each skill does

| Skill | Responsibility |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Clarifies the goal, constraints, and implementation steps before execution. |
| [Workflow](workflow-skill/SKILL.md) | Defines goals, dependencies, resource ownership, and completion for direct or delegated work. |
| [Code](code-skill/SKILL.md) | Guides code structure, readable implementation, and portable, quiet execution. |
| [Prompt](prompt-skill/SKILL.md) | Shapes reusable prompts with clear inputs, constraints, and output contracts. |
| [Verify](verify-skill/SKILL.md) | Checks real behavior or outputs in the active task and keeps test coverage focused. |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls relevant project context and records useful durable changes in Obsidian. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Installs the managed skills recoverably and validates authorized publication. |

## Task flow

1. Ensure the Obsidian vault, then read the applicable skills and matching project memory. Missing memory for the exact project is a normal read skip after vault setup.
2. Briefly describe the objective and implementation steps, then proceed. Do not add a confirmation checkpoint unless a necessary decision or authorization is missing.
3. Finish with a real behavior check inside the active task. Update existing tests where useful, then clean up disposable resources.
4. When useful, record durable changes in the configured Obsidian vault through a separate, unpinned projectless Ending task. Ending does not gate, test, or repair the main result. If the vault is unavailable, keep the write pending without a Codex-local fallback.

Project knowledge is centralized in one Memory.json index and one Knowledge.md view per project. Recall matches the exact project, module, file and method; stale entries stay out of current context. Ending consolidates touched entries and periodically refreshes project summaries and explicit reference links.

Project memories stay isolated. Shared preferences are read only when relevant. Project `AGENTS.md` and Skills own stable operating rules; changing project information and historical outcomes live in Obsidian.

Without a vault, [Project Memory](project-memory-skill/SKILL.md) uses [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki) to create and verify a private Obsidian vault outside Codex and the project. New vaults default to `~/Documents/Obsidian/LLM Memory`; configure `CODEX_OBSIDIAN_VAULT` or `--vault` to choose another location. Back up the entire vault regularly: it holds all Codex and project memory. The generator is a public template, not a private-memory backup.

macOS/Linux: `python3 -B project-memory-skill/scripts/obsidian_vault_setup.py --project-root .`

Windows PowerShell: `py -3 -B project-memory-skill\scripts\obsidian_vault_setup.py --project-root .`

## Source and installation

Install user Skills only in `~/.agents/skills` ([official location](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)). `CODEX_HOME` (default `~/.codex`) owns configuration, global `AGENTS.md`, and system resources. Automatically [repair legacy roots](management-skill/references/skill-directory-repair.md); preserve `.system` and plugins.

Each skill folder owns its `SKILL.md`, references, helpers, and versioned development tests needed by the release gate. Disposable task work belongs in ignored `Cache/temp-*`; retained local evidence belongs in `Cache/remote-*` with an explicit reason and owner.

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

On Windows, use `py -3 -B` with the same Python entry point. Installation replaces the eight managed skills with locking, backup, and recovery, then ensures and reports the Obsidian memory vault. It preserves unrelated skills, user AGENTS, and existing private history. An explicitly requested global AGENTS update uses `install-global-agents --source-dir .` and creates a restorable backup.

Source edits, installed updates, and GitHub publication are distinct. The publisher's `push` command runs the current release gate before staging or remote writes.

## Code reference owners

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [Python](code-skill/references/python-rules.md)
- [Unity C#](code-skill/references/unity-csharp-rules.md)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

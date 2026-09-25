# qin-codex-skills

This repository maintains eight reusable global Codex skills. They guide task analysis, code and prompt work, verification, project memory, and skill installation. The goal is consistent, reviewable work across projects while each project keeps its own domain rules.

The model and reasoning effort you select stay in charge of work governed by these skills. Independent work without a governing skill may use adaptive model selection based on task complexity and verified outcomes from the same project. Mechanical tool calls need no extra model.

## What each skill does

| Skill | Responsibility |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Scores tasks, preserves the selected model and effort, and routes independent work when useful. |
| [Workflow](workflow-skill/SKILL.md) | Defines goals, dependencies, resource ownership, and completion for direct or delegated work. |
| [Code](code-skill/SKILL.md) | Guides code structure, readable implementation, and portable, quiet execution. |
| [Prompt](prompt-skill/SKILL.md) | Shapes reusable prompts with clear inputs, constraints, and output contracts. |
| [Verify](verify-skill/SKILL.md) | Checks real behavior or outputs in the active task and keeps test coverage focused. |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls relevant project context and records useful durable changes in Obsidian. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Installs the managed skills recoverably and validates authorized publication. |

## Task flow

1. Ensure the Obsidian vault, then read the applicable skills and matching project memory. Missing memory for the exact project is a normal read skip after vault setup.
2. Show the task score, selected model and effort, and route. Work directly or delegate independent pieces with explicit ownership and dependencies.
3. Finish and verify the result inside the active task with a real behavior check or output readback. Revise useful existing tests before adding files, and clean up disposable task resources after readback.
4. When useful, record durable changes in the configured Obsidian vault through a separate, unpinned projectless Ending task. Ending does not gate, test, or repair the main result. If the vault is unavailable, keep the write pending without a Codex-local fallback.

Project memories stay isolated. Shared preferences are read only when relevant. Project `AGENTS.md` and Skills own stable operating rules; changing project information and historical outcomes live in Obsidian.

If no memory vault is installed, [Project Memory](project-memory-skill/SKILL.md) connects to [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki), creates a private Obsidian-compatible vault outside Codex and the project, verifies it, and reports its exact location. The default new location is `~/Documents/Obsidian/LLM Memory`; use `CODEX_OBSIDIAN_VAULT` or `--vault` to choose another durable location. Back up the entire vault regularly: it contains all Codex and project memory. The public generator is a template, not a destination for private memory or a backup.

macOS/Linux: `python3 -B project-memory-skill/scripts/obsidian_vault_setup.py --project-root .`

Windows PowerShell: `py -3 -B project-memory-skill\scripts\obsidian_vault_setup.py --project-root .`

## Source and installation

Each skill folder owns its `SKILL.md`, references, helpers, and versioned development tests needed by the release gate. Disposable task work belongs in ignored `Cache/temp-*`; retained local evidence belongs in `Cache/remote-*` with an explicit reason and owner.

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

On Windows, use `py -3 -B` with the same Python entry point. Installation replaces the eight managed skills with locking, backup, and recovery, then ensures and reports the Obsidian memory vault. It preserves unrelated skills, user AGENTS, and private routing history. An explicitly requested global AGENTS update uses `install-global-agents --source-dir .` and creates a restorable backup.

Source edits, installed updates, and GitHub publication are distinct. The publisher's `push` command runs the current release gate before staging or remote writes.

## Code reference owners

- `general` · general · `workflow-skill` · active · [rules](./task-analyze-skill/references/model-selection.md)
- `python` · code · `code-skill` · active · [rules](./code-skill/references/python-rules.md)
- `csharp` · code · `code-skill` · history-only · [rules](./code-skill/references/csharp-rules.md)
- `unity_csharp` · code · `code-skill` · active · [rules](./code-skill/references/unity-csharp-rules.md)
- `code_unspecified` · code · `code-skill` · history-only · [rules](./code-skill/references/legacy-code-unspecified.md)

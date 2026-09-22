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
| [Project Memory](project-memory-skill/SKILL.md) | Recalls relevant project context and records useful durable changes locally. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Installs the managed skills recoverably and validates authorized publication. |

## Task flow

1. Read the applicable skills and matching project memory, then define the goal and evidence needed. Missing memory is a normal skip.
2. Show the task score, selected model and effort, and route. Work directly or delegate independent pieces with explicit ownership and dependencies.
3. Finish and verify the result inside the active task with a real behavior check or output readback. Revise useful existing tests before adding files, and clean up disposable task resources after readback.
4. When useful, record durable changes in local memory through a separate, unpinned projectless Ending task. Ending does not gate, test, or repair the main result.

Project memories stay isolated. Shared preferences are read only when relevant.

## Source and installation

Each skill folder owns its `SKILL.md`, references, helpers, and versioned development tests needed by the release gate. Disposable task work belongs in ignored `Cache/temp-*`; retained local evidence belongs in `Cache/remote-*` with an explicit reason and owner.

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

On Windows, use `py -3 -B` with the same Python entry point. Installation replaces the eight managed skills with locking, backup, and recovery. It preserves unrelated skills, user AGENTS, and private routing history. An explicitly requested global AGENTS update uses `install-global-agents --source-dir .` and creates a restorable backup.

Source edits, installed updates, and GitHub publication are distinct. The publisher's `push` command runs the current release gate before staging or remote writes.

## Code reference owners

<!-- EXECUTION_DOMAIN_TABLE -->

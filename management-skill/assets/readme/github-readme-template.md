# qin-codex-skills

Concise global skills for code structure, UI preferences, task coordination, and project memory.

The model you select reads relevant skills and project memory, understands the task, and defines specific goals. Work governed by those skills keeps your selected model **and reasoning effort**. Independent routine work can still use adaptive model selection; mechanical tool calls need no extra model.

## Workflow

1. Read applicable skills and matching project memory. Missing memory is a normal skip.
2. Show the task score, selected model/effort and route. Execute directly or plan useful dependencies; disclose delegated goals, scores, pairs, dependencies and outcomes.
3. Verify changed code and consequential results inside the task with one real behavior check or output readback. Whole-project startup or compilation requires requested scope.
4. Complete the result, then summarize useful durable changes in local memory with the selected model. Ending is a separate unpinned projectless task in recent tasks; its status does not gate the main task, and it never tests or repairs.

Project memories stay isolated. Shared preferences are read only when relevant. Current summaries retain code structure, UI design choices, document organization, and important decisions without duplicating task transcripts.

## Skills

| Skill | Core idea |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Preserve selected models for governed work; adapt independent work. |
| [Workflow](workflow-skill/SKILL.md) | Clear goals, useful plans, safe parallel ownership. |
| [Code](code-skill/SKILL.md) | Direct readable code, explicit responsibilities, consistent UI. |
| [Prompt](prompt-skill/SKILL.md) | Clear goals, constraints, inputs, and output contracts. |
| [Verify](verify-skill/SKILL.md) | Focused evidence before completion. |
| [Project Memory](project-memory-skill/SKILL.md) | Relevant recall and concise durable summaries. |
| [Optimization](optimization-skill/SKILL.md) | Requested simplification with measured results. |
| [Management](management-skill/SKILL.md) | Recoverable installation and authorized publication. |

## Install or update

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

On Windows, use `py -3 -B` with the same Python entry point. Installation replaces the eight managed skills with locking, backup, and recovery. It preserves unrelated skills, user AGENTS, and private routing history. An explicitly requested global AGENTS update uses `install-global-agents --source-dir .` and creates a restorable backup.

Source edits, installed updates, and GitHub publication are distinct. The publisher's `push` command runs the current release gate before staging or remote writes.

## Code reference owners

<!-- EXECUTION_DOMAIN_TABLE -->

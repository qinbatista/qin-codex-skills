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

1. At startup/resume, [check the current task project's AI index](management-skill/references/project-ai-index.md): request first-bootstrap consent; otherwise reuse focused routes. Never prompt or maintain indexes in reference projects. Ensure Obsidian memory, skip missing memory, and track Skill use.
2. Preview the objective and implementation steps, then execute. Ask only for necessary decisions or authorization.
3. For every task that changes the project, update and verify its relevant AI-index guidance before delivery. Reconcile root `AGENTS.md` when needed. Consult project testing Skills; run real affected-case checks and clean disposable resources.
4. Close out guidance, memory and resources in the active task under [Project Memory](project-memory-skill/SKILL.md) and [Workflow](workflow-skill/SKILL.md). Codex chats and sessions remain user-managed; do not create or delete an Ending chat automatically.

At completion, summarize actual Skill names, steps and reasons once, including branch use; distinguish unused, missing or unreadable Skills. Progress updates need no repeated lists; [reporting is mandatory](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting).

Project memories stay isolated in Memory.json and Knowledge.md. Recall excludes stale facts. The active task consolidates touched entries and shared preferences remain scoped. `AGENTS.md` and Skills own stable rules; changing facts and history live in Obsidian.

Repository work and installers use `--existing-only`; missing vaults remain pending. First-vault setup with [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki) requires explicit authorization through [Project Memory](project-memory-skill/SKILL.md). Back up the whole vault containing Codex and project memory; the generator contains no private memories.

macOS/Linux: `python3 -B project-memory-skill/scripts/obsidian_vault_setup.py --project-root . --existing-only`

Windows PowerShell: `py -3 -B project-memory-skill\scripts\obsidian_vault_setup.py --project-root . --existing-only`

## Install the global Skill pack

Save [install_skill_pack.py](https://raw.githubusercontent.com/qinbatista/qin-codex-skills/master/management-skill/scripts/install_skill_pack.py) and run the command for your operation. Use `py -3 -B` on Windows.

```text
python3 -B install_skill_pack.py install qin-codex-skills
python3 -B install_skill_pack.py update qin-codex-skills
python3 -B install_skill_pack.py uninstall qin-codex-skills
```

Codex loads the Skills directly from `~/.agents/skills/qin-codex-skills/<skill>/SKILL.md`. The directory contains the pack manifest and each Skill's files. READMEs, AGENTS, project indexes and tests stay in source. [Codex user Skill locations](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

Update downloads the current `codex/plugin` package and replaces the whole directory. Uninstall removes the pack directory. When switching from the old Marketplace installation, also run `codex plugin remove qin-codex-skills@qin-codex-skills` and `codex plugin marketplace remove qin-codex-skills` to remove its previous copy.

## Maintain the source

GitHub Actions publishes the package from `master` to `codex/plugin`. The [source publisher](management-skill/SKILL.md#publish) uses `--include-path` and `--include-commit` to verify and deliver selected changes through the configured upstream.

Keep disposable development files in a fresh ignored `Cache/temp-<task>/` run under [the project Cache policy](workflow-skill/references/project-cache-artifact-policy.md).

## Code reference owners

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [State, async results and side effects](code-skill/references/state-and-side-effects.md)
- [Actual target and evidence boundaries](verify-skill/SKILL.md#bind-evidence-to-the-actual-target)
- [Python](code-skill/references/python-rules.md)
- [Unity Code](https://github.com/qinbatista/qin-unity-skills/tree/master/unity-code-skill)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

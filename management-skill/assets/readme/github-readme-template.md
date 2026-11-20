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

[AI Index Compression](management-skill/references/project-ai-index.md#ai-index-compression) reviews oversized project guidance against current source and scoped Obsidian memory during tasks, preserving rules and history.

All code edits, including tests, follow module → file → method/anchor → necessary relationships plus scoped memory. Selected routes return bounded current excerpts; edits refresh touched routes. Prefer cohesive methods, parameterized variants and deliberate extraction.

Repository work and installers use `--existing-only`; missing vaults remain pending. First-vault setup with [qin-llm-wiki](https://github.com/qinbatista/qin-llm-wiki) requires explicit authorization through [Project Memory](project-memory-skill/SKILL.md). Back up the whole vault containing Codex and project memory; the generator contains no private memories.

macOS/Linux: `python3 -B project-memory-skill/scripts/obsidian_vault_setup.py --project-root . --existing-only`

Windows PowerShell: `py -3 -B project-memory-skill\scripts\obsidian_vault_setup.py --project-root . --existing-only`

## Install the global plugin

Use a Codex CLI with `codex plugin add` support. Run these commands from any folder. Codex enables the plugin for your user across projects.

```text
codex plugin marketplace add qinbatista/qin-codex-skills --ref codex/plugin
codex plugin add qin-codex-skills@qin-codex-skills
```

Open a new Codex session after installing or updating. In the Skills picker, select a Skill from **Qin Codex Skills**. Use `codex plugin list --json` to check the installed and enabled state.

The installed plugin is under `$CODEX_HOME/plugins/cache/qin-codex-skills/qin-codex-skills/`, in a version directory managed by Codex. `CODEX_HOME` normally resolves to `~/.codex`. The package contains `plugin.json` and `skills/` with the eight `SKILL.md` entries and their references, runtime scripts, assets, and display metadata. Repository README files, `AGENTS.md`, the project AI index and tests live on the source branch. See [OpenAI's installation and layout documentation](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work).

## Update or uninstall

Remove the installed plugin and its registered Git marketplace in this order.

```text
codex plugin remove qin-codex-skills@qin-codex-skills
codex plugin marketplace remove qin-codex-skills
```

To update, repeat both install commands after removal. This fetches the current `codex/plugin` branch and installs a fresh copy, so files removed from the release disappear. For removal only, stop after the two commands above.

## Maintain the source

GitHub Actions publishes the package from `master` to `codex/plugin`. Use the [project AI index](skills/ai-index/SKILL.md) to find development and release tools. Keep task support in a fresh project `Cache/temp-<task>/` run under [the artifact policy](workflow-skill/references/project-cache-artifact-policy.md). Release disposable directories and preserve the project's source and active resources.

Source, installation and publication are distinct. The [source publisher](management-skill/SKILL.md#publish) selects files with `--include-path` and existing commits with `--include-commit` full hashes. It integrates, verifies, pushes and reads back the configured upstream, preserving unselected worktree and index changes.

## Code reference owners

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [State, async results and side effects](code-skill/references/state-and-side-effects.md)
- [Actual target and evidence boundaries](verify-skill/SKILL.md#bind-evidence-to-the-actual-target)
- [Python](code-skill/references/python-rules.md)
- [Unity Code](https://github.com/qinbatista/qin-unity-skills/tree/master/unity-code-skill)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

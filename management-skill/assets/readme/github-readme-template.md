# qin-codex-skills

This repository maintains eight global Codex skills for general software work.

## Install the global Skill pack

Paste this into an AI assistant with a local terminal.

```text
Install qin-codex-skills on this computer using the Python 3 installer at
https://raw.githubusercontent.com/qinbatista/qin-codex-skills/master/management-skill/scripts/install_skill_pack.py
Run its install qin-codex-skills action and verify the eight SKILL.md files
under ~/.agents/skills/qin-codex-skills/. Report the installed Skill names.
```

For manual setup, save [install_skill_pack.py](https://raw.githubusercontent.com/qinbatista/qin-codex-skills/master/management-skill/scripts/install_skill_pack.py) and run it from the download directory.

| Host | Command |
| --- | --- |
| macOS or Linux | `python3 -B install_skill_pack.py install qin-codex-skills` |
| Windows PowerShell | `py -3 -B install_skill_pack.py install qin-codex-skills` |

Check `~/.agents/skills/qin-codex-skills/<skill>/SKILL.md` and select `$code-skill` in Codex. `install_skill_pack.py update qin-codex-skills` replaces the whole directory from the published package. `install_skill_pack.py uninstall qin-codex-skills` removes the pack. [Installation checks](management-skill/assets/readme/examples.md#check-an-installation-and-publish-source) · [Codex Skill discovery](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

## What each skill does

| Skill | What it does | Worked example |
| --- | --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Defines the result and follows work through delivery. | [Fix a CSV import](management-skill/assets/readme/examples.md#define-the-finish-line) |
| [Workflow](workflow-skill/SKILL.md) | Coordinates execution, recovery and cleanup. | [Retry a build or test](management-skill/assets/readme/examples.md#retry-a-build-or-test) |
| [Code](code-skill/SKILL.md) | Guides ownership, structure and portable code. | [Write Python](management-skill/assets/readme/examples.md#write-a-python-input-boundary) · [Organize a project](management-skill/assets/readme/examples.md#organize-a-project) · [Replay the Python coding tests](https://github.com/qinbatista/qin-codex-skills/blob/master/.agents/skills/testing-skill/references/codex-python-writing.md) |
| [Prompt](prompt-skill/SKILL.md) | Specifies repeatable AI behavior and output. | [Define a JSON response](management-skill/assets/readme/examples.md#specify-a-prompt-response) |
| [Verify](verify-skill/SKILL.md) | Checks the actual behavior or output. | [Exercise the importer](management-skill/assets/readme/examples.md#verify-the-real-entry-point) |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls and records durable project facts in Obsidian. | [Recall a method contract](management-skill/assets/readme/examples.md#recall-and-record-project-decisions) |
| [Optimization](optimization-skill/SKILL.md) | Improves a selected path and measures the gain. | [Measure batch parsing](management-skill/assets/readme/examples.md#measure-an-optimization) |
| [Management](management-skill/SKILL.md) | Maintains AI indexes, installations and release checks. | [Verify and deliver a pack](management-skill/assets/readme/examples.md#check-an-installation-and-publish-source) |

## Task flow

1. Check the [current project's AI index](management-skill/references/project-ai-index.md), request consent for first creation and use the existing routes for an indexed project. Recall scoped facts and skip missing memory.
2. Review the objective and implementation steps, then execute. Use project testing Skills and real affected-case checks.
3. Update the relevant index for every project change and finish guidance, memory and cleanup in the active task. Codex chats and sessions remain user-managed.

Project memories stay isolated in the configured Obsidian vault. At completion, summarize actual Skill names, steps and reasons once. [Routing guide](task-analyze-skill/references/global-skill-routing.md) · [Reporting](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting)

## Maintain the source

GitHub Actions keeps the native marketplace files current on `master`. The grouped installer reads the Skill package from the `master` archive. The [source publisher](management-skill/SKILL.md#publish) takes exact `--include-path` or `--include-commit` selections and delivers through the configured upstream. Keep disposable files in an ignored `Cache/temp-<task>/` work directory. [Cache policy](workflow-skill/references/project-cache-artifact-policy.md)

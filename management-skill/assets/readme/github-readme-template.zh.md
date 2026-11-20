# qin-codex-skills

This repository maintains eight reusable global Codex Skills for task analysis, code and prompt authoring, verification, project memory, installation, and publication. The Skills make work consistent and verifiable across projects. Each project owns its domain rules.

Preview the objective and the implementation steps before starting. The user can steer or stop the work at any time. Pause only for necessary information or authorization.

## Skill responsibilities

| Skill | Responsibility |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Tracks Skill use, clarifies the objective, requires delivery, and recovers from failures. |
| [Workflow](workflow-skill/SKILL.md) | Coordinates work and resource cleanup while preserving active resources and review or reuse inputs. |
| [Code](code-skill/SKILL.md) | Guides code structure, clear implementation, and portable, quiet execution. |
| [Prompt](prompt-skill/SKILL.md) | Defines inputs, constraints, and output contracts for reusable prompts. |
| [Verify](verify-skill/SKILL.md) | Checks actual behavior or output in the active task and focuses test coverage. |
| [Project Memory](project-memory-skill/SKILL.md) | Recalls relevant project context and records useful durable changes in Obsidian. |
| [Optimization](optimization-skill/SKILL.md) | Simplifies requested code or workflows and measures claimed improvements. |
| [Management](management-skill/SKILL.md) | Installs managed Skills recoverably and verifies authorized publication. |

## Task flow

1. At startup or resume, [check the current project's AI index](management-skill/references/project-ai-index.md). If it is missing, obtain first-bootstrap consent before reading rules or creating it. Ask again at the next startup if it remains absent. Reference lookups leave the current project unchanged and trigger no index prompt or maintenance. Reuse focused module rules in an existing index, ensure the Obsidian vault is available, recall scoped project facts, skip absent matching memory, and track actual Skill use.
2. Preview the objective and steps, then execute. Report material changes to the approach as they occur.
3. For every task that changes the project, update and verify its relevant AI-index guidance before delivery. Reconcile root `AGENTS.md` when needed. Read the project testing Skill before adding a maintained test. Verify the real affected case, fix failures, and release disposable resources.
4. Close out guidance, memory, and resources in the active task under [Project Memory](project-memory-skill/SKILL.md) and [Workflow](workflow-skill/SKILL.md). Preserve active resources and resources needed for review or reuse.

Use progress updates for material developments. At completion, report the exact Skills used, what they did, and why, including branch work. Identify unused, missing, or unreadable Skills separately. Follow the [mandatory reporting rules](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting).

Project memory lives in each project's `Memory.json` with a readable `Knowledge.md` view. Recall by exact project, module, file, and method. Exclude stale entries from current context. Consolidate touched entries, maintain due project synthesis, and keep references explicit. Each project owns its own memory, and shared preferences are selected only when relevant.

The global workflow checks the current project's local index at startup, on applicable changes, and at finish. Each project retains its own index. The helper validates routes and applies reviewed changes against source evidence and file hashes. Index maintenance is part of task execution, and reviewed rules determine the index structure.

For local code changes, including tests, locate the module, file, method or key-line anchor, and necessary relationships. Recall exact-scope memory and verify current source. Keep stable responsibilities and entry points in the index. Selected routes return bounded source excerpts. Keep related behavior cohesive, parameterize variants when appropriate, and refresh routes touched by a change.

Write project documentation, Skills, `AGENTS.md`, AI-index guidance, and durable memory in English. Follow [Management's authoring rules](management-skill/SKILL.md#authoring-rules).

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

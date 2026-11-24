# Qin global Skill routing

Apply the current project's startup and source-owner rules first. Select by the requested work and actual project context. Open the matched installed `SKILL.md` before the corresponding work, including when the user does not name a Skill. A Skill name or description alone does not load its workflow.

The global pack root is `~/.agents/skills`. The paths in this guide are below that root. Use the installed Skill's own references when it selects them. If an optional pack is absent, report that entry as unavailable and use the applicable project workflow.

| Work | Required entry |
| --- | --- |
| Start, scope, resume, or close project work | `qin-codex-skills/task-analyze-skill/SKILL.md` |
| Coordinate work, Git delivery or waits. Manage task resources from acquisition to release, including compute jobs, memory, research tabs, previews and test folders. | `qin-codex-skills/workflow-skill/SKILL.md` |
| Write, refactor, repair, or review code and run language-neutral or Python checks | `qin-codex-skills/code-skill/SKILL.md` |
| Create, edit, or test a reusable prompt or durable AI instructions | `qin-codex-skills/prompt-skill/SKILL.md` |
| Select verification evidence or verify changed behavior and consequential outputs | `qin-codex-skills/verify-skill/SKILL.md` |
| Plan local execution for repeatable tests, diagnostics, or multi-step operations, or optimize an existing code path or workflow | `qin-codex-skills/optimization-skill/SKILL.md` |
| Recall or maintain project knowledge in Obsidian | `qin-codex-skills/project-memory-skill/SKILL.md` |
| Maintain Skills, manage installation, or maintain project AI indexes | `qin-codex-skills/management-skill/SKILL.md` |

For language, platform or feature-specific work, also match the descriptions of other installed Skills. When a matching pack supplies its own `*/references/global-skill-routing.md`, read it and open the entries it selects. Otherwise open the matching Skill directly. Code supplies the shared writing rules and Verify the evidence standards.

## Require routing across projects

Set `developer_instructions` in the Codex user `config.toml` under `CODEX_HOME` (default `~/.codex`). Append the paragraph to the existing value when that key is already present. [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)

```toml
developer_instructions = """
For tasks involving Qin's project workflow, code, prompts, verification, optimization, project memory, Skill management or another installed Qin Skill, follow the applicable project's startup and source-owner rules. Read ~/.agents/skills/qin-codex-skills/task-analyze-skill/references/global-skill-routing.md and open every matching installed SKILL.md before the corresponding work, even if the user does not name a Skill.
"""
```

Verify in a fresh session with an ordinary task and check that it opens the installed Skill. Remove the routing paragraph from the user setting when uninstalling the pack.

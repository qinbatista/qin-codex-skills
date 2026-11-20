# Qin global Skill routing

Apply the current project's startup and source-owner rules first. Select by the requested work and actual project context. Open the matched installed `SKILL.md` before the corresponding work, including when the user does not name a Skill. A Skill name or description alone does not load its workflow.

The global pack root is `~/.agents/skills`. The paths in this guide are below that root. Use the installed Skill's own references when it selects them. If an optional pack is absent, report that entry as unavailable and use the applicable project workflow.

| Work | Required entry |
| --- | --- |
| Start, scope, resume, or close project work | `qin-codex-skills/task-analyze-skill/SKILL.md` |
| Coordinate work, tasks, Git delivery, waits, or Cache and resource cleanup | `qin-codex-skills/workflow-skill/SKILL.md` |
| Write, refactor, repair, or review code and run language-neutral or Python checks | `qin-codex-skills/code-skill/SKILL.md` |
| Create, edit, or test a reusable prompt or durable AI instructions | `qin-codex-skills/prompt-skill/SKILL.md` |
| Select verification evidence or verify changed behavior and consequential outputs | `qin-codex-skills/verify-skill/SKILL.md` |
| Simplify, optimize, or measure an existing code path or workflow | `qin-codex-skills/optimization-skill/SKILL.md` |
| Recall or maintain project knowledge in Obsidian | `qin-codex-skills/project-memory-skill/SKILL.md` |
| Maintain Skills, manage installation, or maintain project AI indexes | `qin-codex-skills/management-skill/SKILL.md` |
| Write or review C# and change Unity gameplay, serialized state, Jobs, resources, or SDK integrations | `qin-unity-skills/unity-code-skill/SKILL.md` |
| Place, move, or import Unity Prefabs, scenes, textures, Sprites, or other assets | `qin-unity-skills/unity-assets-skill/SKILL.md` |
| Change Unity UI Toolkit or Canvas, screen layout, navigation, or insets | `qin-unity-skills/unity-ui-skill/SKILL.md` |
| Change Unity clips, Animator states, motion timing, bones, or rig transfer | `qin-unity-skills/unity-animation-skill/SKILL.md` |
| Change Unity particles, VFX, shaders, or material effects | `qin-unity-skills/unity-effects-skill/SKILL.md` |
| Verify Unity Editor, Play Mode, Player, device, build, or profiling behavior | `qin-unity-skills/unity-testing-skill/SKILL.md` |

Code owns shared code policy. Unity Code owns C# and engine behavior, with only the common C# rules applying outside Unity. Verify owns evidence standards. Unity Testing selects the real Unity runner and runtime. Use Assets for imports and serialized references, UI for screen structure and input, Animation for motion playback, and Effects for appearance and emission. Apply additional entries only for work the task actually crosses. A linked game follows its current YoFaAssets source and local game rules before the reusable Unity guidance.

To require this routing across repositories, reference this installed guide from the Codex user `developer_instructions` setting. Preserve any existing instruction text. A fresh session should open the matching Skill for an ordinary task without an explicit Skill mention.

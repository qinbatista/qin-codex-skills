# qin-codex-skills

本仓库维护八个可复用的全局 Codex Skill。它们指导任务分析、代码和提示词编写、结果验证、项目记忆以及 Skill 的安装与发布。目标是让不同项目中的工作方式一致且可检查，同时由各项目保管自己的领域规则。

执行前先简述任务目标和大概实现步骤，让用户了解接下来要做什么，再按步骤执行。用户可以随时调整或中止；只有缺少必要信息或授权时才停下来询问。

## 各 Skill 的职责

| Skill | 职责 |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | 全程显示 Skill 名称与用途，明确目标、完成工作并处理可恢复的失败。 |
| [Workflow](workflow-skill/SKILL.md) | 协调任务及全局资源清理，保留正在使用和用户审阅/复用所需的资源。 |
| [Code](code-skill/SKILL.md) | 指导代码结构、清晰实现以及跨平台、安静的执行方式。 |
| [Prompt](prompt-skill/SKILL.md) | 为可复用提示词明确输入、约束和输出约定。 |
| [Verify](verify-skill/SKILL.md) | 在当前任务内验证真实行为或输出，并控制测试覆盖范围。 |
| [Project Memory](project-memory-skill/SKILL.md) | 读取相关项目上下文，并在本地记录值得保留的变化。 |
| [Optimization](optimization-skill/SKILL.md) | 简化用户要求的代码或流程，并实测所声称的改进。 |
| [Management](management-skill/SKILL.md) | 可恢复地安装托管 Skill，并验证获授权的发布。 |

## 任务流程

1. 每次启动或恢复任务时，首次调用工具前先列出准备使用的 Skill 准确名称与简短用途，再读取适用的 Skill 和当前项目记忆，确定目标及所需证据；记忆缺失时直接跳过。
2. 先简述目标和实现步骤，再按步骤执行；步骤发生重要变化时及时说明。
3. 完成要求的修改，并在当前任务内用真实行为检查或输出回读验证。修复可恢复的失败；分别报告已交付的修改与有证据的阻碍。优先修改有用的现有测试，再清理一次性任务资源。
4. 使用一个获授权、未置顶的无项目 Ending 任务，并行整理 Obsidian 本地记忆和[审查已完成任务的资源](workflow-skill/references/ending-resource-audit.md)。先遵循资源所属 Skill 的清理流程，再补充清理遗漏的一次性 Cache、浏览器/预览/终端、进程和网络资源。保留正在使用及用户审阅或复用所需的文件和环境。记忆库不可用不阻碍清理；Ending 不阻碍、测试或修复主任务结果。

每条进度更新和阶段切换都必须重复列出 Skill 准确名称与简短用途，包括并行分支。新增 Skill 先声明再使用，区分准备使用和实际应用；结束时列出全部实际用过的 Skill 及各自完成的工作。没有适用 Skill、缺失或未使用也要如实说明，不能因简短而省略[强制报告](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting)。

项目记忆集中在每个项目的一份 Memory.json 索引和一份 Knowledge.md 总览中。按项目、模块、文件和方法精确读取，过时记录不作为当前事实。Ending 每次整理涉及的条目，并定期更新项目总结与明确的参考关联。

项目记忆互相隔离；只读取明确相关的共享偏好。

## 源码与安装

用户 Skill 默认统一安装到官方目录 `~/.agents/skills`，参见 [Codex 官方说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。`CODEX_HOME`（默认 `~/.codex`）仍负责配置、全局 `AGENTS.md` 和系统内置资源。发现旧目录或旧引用时按[自动修复流程](management-skill/references/skill-directory-repair.md)处理；项目 Skill 保持在项目内，迁移保留 `.system`、插件和可恢复备份。

Skill 目录只保存指令、引用、辅助脚本和版本化发布测试。临时截图、JSON 回执、测试输出从首次写入起只能进入已忽略的 `Cache/temp-<task>/`，不得提交到 Git；无项目任务使用其工作区 Cache。交付或最小恢复状态转交并回读后删除一次性文件；保留用户审阅或复用所需文件及其底层资源，待真实所有者和引用验证后再清理。`remote-*` 名称本身不证明保留权。

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

Windows 使用 `py -3 -B`。安装以锁、备份和恢复机制替换八个托管 Skill，保留其他 Skill、用户 AGENTS 和已有私人历史。明确更新全局 AGENTS 时使用 `install-global-agents --source-dir .`，并生成可恢复备份。

源代码修改、本地安装和 GitHub 发布是不同结果。发布命令 `push` 在暂存或远端写入前运行当前发布检查。

## 代码规则归属

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [Python](code-skill/references/python-rules.md)
- [Unity C#](code-skill/references/unity-csharp-rules.md)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

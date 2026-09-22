# qin-codex-skills

本仓库维护八个可复用的全局 Codex Skill。它们指导任务分析、代码和提示词编写、结果验证、项目记忆以及 Skill 的安装与发布。目标是让不同项目中的工作方式一致且可检查，同时由各项目保管自己的领域规则。

受这些 Skill 约束的工作始终使用用户选择的**模型和推理强度**。不受 Skill 约束的独立任务可根据任务复杂度和同项目已验证的结果调整模型。纯工具调用无需额外模型。

## 各 Skill 的职责

| Skill | 职责 |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | 评估任务复杂度，保留所选模型与推理强度，并在适合时为独立工作选择模型。 |
| [Workflow](workflow-skill/SKILL.md) | 为直接执行或委派的工作明确目标、依赖、资源归属和完成条件。 |
| [Code](code-skill/SKILL.md) | 指导代码结构、清晰实现以及跨平台、安静的执行方式。 |
| [Prompt](prompt-skill/SKILL.md) | 为可复用提示词明确输入、约束和输出约定。 |
| [Verify](verify-skill/SKILL.md) | 在当前任务内验证真实行为或输出，并控制测试覆盖范围。 |
| [Project Memory](project-memory-skill/SKILL.md) | 读取相关项目上下文，并在本地记录值得保留的变化。 |
| [Optimization](optimization-skill/SKILL.md) | 简化用户要求的代码或流程，并实测所声称的改进。 |
| [Management](management-skill/SKILL.md) | 可恢复地安装托管 Skill，并验证获授权的发布。 |

## 任务流程

1. 读取适用的 Skill 和当前项目记忆，再确定目标及所需证据；记忆缺失时直接跳过。
2. 展示任务评分、所选模型与推理强度及执行路线。直接执行，或以明确的归属和依赖委派独立工作。
3. 在当前任务内用真实行为检查或输出回读完成验证。优先修改有用的现有测试，并在回读后清理一次性任务资源。
4. 如有值得长期保留的信息，使用独立、未置顶的无项目 Ending 任务写入本地记忆。Ending 不阻碍、测试或修复主任务结果。

项目记忆互相隔离；只读取明确相关的共享偏好。

## 源码与安装

每个 Skill 目录负责自己的 `SKILL.md`、参考规则、工具和发布检查所需的版本化开发测试。一次性任务文件放在忽略提交的 `Cache/temp-*`；有明确保留原因和负责人的本地证据放在 `Cache/remote-*`。

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

Windows 使用 `py -3 -B`。安装以锁、备份和恢复机制替换八个托管 Skill，保留其他 Skill、用户 AGENTS 和私有路由历史。明确更新全局 AGENTS 时使用 `install-global-agents --source-dir .`，并生成可恢复备份。

源代码修改、本地安装和 GitHub 发布是不同结果。发布命令 `push` 在暂存或远端写入前运行当前发布检查。

## 代码规则归属

<!-- EXECUTION_DOMAIN_TABLE -->

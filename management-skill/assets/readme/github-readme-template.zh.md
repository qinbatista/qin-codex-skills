# qin-codex-skills

本仓库维护八个可复用的全局 Codex Skill。它们指导任务分析、代码和提示词编写、结果验证、项目记忆以及 Skill 的安装与发布。目标是让不同项目中的工作方式一致且可检查，同时由各项目保管自己的领域规则。

执行前先简述任务目标和大概实现步骤，让用户了解接下来要做什么，再按步骤执行。用户可以随时调整或中止；只有缺少必要信息或授权时才停下来询问。

## 各 Skill 的职责

| Skill | 职责 |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | 记录 Skill 用途并在结尾汇总，明确目标、完成工作并处理可恢复的失败。 |
| [Workflow](workflow-skill/SKILL.md) | 协调任务及全局资源清理，保留正在使用和用户审阅/复用所需的资源。 |
| [Code](code-skill/SKILL.md) | 指导代码结构、清晰实现以及跨平台、安静的执行方式。 |
| [Prompt](prompt-skill/SKILL.md) | 为可复用提示词明确输入、约束和输出约定。 |
| [Verify](verify-skill/SKILL.md) | 在当前任务内验证真实行为或输出，并控制测试覆盖范围。 |
| [Project Memory](project-memory-skill/SKILL.md) | 读取相关项目上下文，并在本地记录值得保留的变化。 |
| [Optimization](optimization-skill/SKILL.md) | 简化用户要求的代码或流程，并实测所声称的改进。 |
| [Management](management-skill/SKILL.md) | 可恢复地安装托管 Skill，并验证获授权的发布。 |

## 任务流程

1. 每次启动或恢复任务时，先[轻量检查项目 AI 索引](management-skill/references/project-ai-index.md)。缺失时先征得同意，再读取规则并创建；未完成则下次启动再次提醒。已有索引直接复用相关模块规则；确保 Obsidian 记忆库可用，按项目精确回忆并记录实际 Skill 用途，缺少匹配记忆时直接跳过。
2. 先简述目标和实现步骤，再按步骤执行；步骤发生重要变化时及时说明。
3. 用户已确认的项目意图或结构变化时，以及交付前，自动更新精简的根 `AGENTS.md` 与 `.agents/skills/ai-index`。新增维护测试前先读项目测试 Skill，默认验证真实受影响场景，修复失败并清理一次性资源。
4. 创建独立、未置顶的 Ending 前先核实所属服务的原生删除能力；没有可用路径时，在当前聊天完成收尾，不创建新会话。有可用路径时，显示创建链接后立即结束主线程，不等待 Ending。Ending 自行整理本地记忆、[审查资源](workflow-skill/references/ending-resource-audit.md)、恢复并执行原生删除及回读。保留活动和审阅/复用资源；归档不能代替删除。

进度更新只报告工作进展，无需重复列出 Skill。结尾一次性汇总实际使用的 Skill 准确名称、对应步骤和原因，包括并行分支；未使用、缺失或不可读的 Skill 另行如实说明，没有适用 Skill 时说明原因。参见[强制报告规则](task-analyze-skill/SKILL.md#mandatory-visible-skill-reporting)。

项目记忆集中在每个项目的一份 Memory.json 索引和一份 Knowledge.md 总览中。按项目、模块、文件和方法精确读取，过时记录不作为当前事实。Ending 每次整理涉及的条目，并定期更新项目总结与明确的参考关联。

项目记忆互相隔离；只读取明确相关的共享偏好。

AI 索引由全局工作流在开始、变化和结束时自动检查维护，无需用户重复要求；每个项目独立保管，不放入全局或插件 Skill。辅助脚本检查路由，并核对源码和原文件指纹后应用已审阅的更新。Ending 使用同一规则核对和整理根指导与项目索引，不修改产品代码或自行发布。这是代理工作流，不是后台监控进程；脚本不凭文件名猜测项目含义。

## 源码与安装

用户 Skill 默认统一安装到官方目录 `~/.agents/skills`，参见 [Codex 官方说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。`CODEX_HOME`（默认 `~/.codex`）仍负责配置、全局 `AGENTS.md` 和系统内置资源。发现旧目录或旧引用时按[自动修复流程](management-skill/references/skill-directory-repair.md)处理；项目 Skill 保持在项目内，迁移保留 `.system`、插件和可恢复备份。

Skill 目录只保存指令、引用、辅助脚本和版本化发布测试。[外部任务产物规则](workflow-skill/references/project-cache-artifact-policy.md)要求所有 AI 临时支持、截图、回执、测试输出和工具缓存从首次写入起位于项目目录和 Codex 管理目录之外，不得进入 Git。统一解析器使用 `YOFA_TASK_ARTIFACT_ROOT` 或当前平台发现的 `YoFaAI/TaskArtifacts` 基址，按准确项目、任务和执行隔离；同一窗口/聊天的每次请求、续测、构建、打包或部署也分配新的 `temp-*`。继续工作只复制有用输入并回读字节，完成的旧目录和一次性 worktree 立即按 owner 回收，不等整条聊天结束。正式源码、交付、运行时和素材保留原 owner；旧临时文件只在归属、使用方、字节和引用核验后迁移。交付或最小恢复状态回读后清理一次性支持，保留用户审阅和复用资源；`remote-*` 名称本身不证明保留权。

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

Windows 使用 `py -3 -B`。安装以锁、备份和恢复机制替换八个托管 Skill，保留其他 Skill、用户 AGENTS 和已有私人历史。明确更新全局 AGENTS 时使用 `install-global-agents --source-dir .`，并生成可恢复备份。

强制 AI-index 启动提问需要始终加载的全局入口，单独安装 Skill 不会自动触发。获得授权后，用同一安装器执行 `install-global-agents --source-dir . --startup-only`，只更新启动区块并保留个人规则。普通部署会提示入口缺失、过期或被全局 override 遮蔽，不会擅自覆盖。请用新的 Codex 会话验证；已运行的会话可能仍保留旧指令。

源代码修改、本地安装和 GitHub 发布是不同结果。发布命令 `push` 用重复的 `--include-path` 明确选择本任务文件；已有的本任务本地提交用 `--include-commit` 完整哈希选择。发布通过当前分支已有上游完成合并、发布检查、正常推送和远端回读，并保留未选择的工作区及索引修改。

## 代码规则归属

- [Code philosophy](code-skill/references/code-writing-philosophy.md)
- [状态、异步结果与副作用](code-skill/references/state-and-side-effects.md)
- [实际运行对象与验收范围](verify-skill/SKILL.md#bind-evidence-to-the-actual-target)
- [Python](code-skill/references/python-rules.md)
- [Unity C#](code-skill/references/unity-csharp-rules.md)
- [Portable quiet execution](code-skill/references/skill-platform-compatibility.md)

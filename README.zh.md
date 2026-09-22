# qin-codex-skills

精简的全局 Skill：代码结构、UI 偏好、任务协作与项目记忆。

用户选择的模型负责阅读相关 Skill 和项目记忆，理解任务并定义各子任务目标。受 Skill 约束的工作保留用户选择的**模型和推理强度**；独立且不受 Skill 约束的常规工作仍可自适应选模。纯工具调用无需额外模型。

## 工作流程

1. 读取相关 Skill 和当前项目记忆；记忆缺失直接跳过。
2. 展示任务评分、模型/推理强度和路由；子任务展示目标、评分、模型、依赖和结果。简单任务直接执行；需要时计划依赖，把独立目标交给写入范围清晰的子任务。
3. 在当前任务内用真实行为检查或输出回读验证代码改动及重要结果。只有用户要求相应范围时才启动或编译整个项目。
4. 主任务完成后，用用户选择的模型将值得保留的信息写入本地记忆。Ending 是最近任务列表中独立、未置顶的无项目任务；它的状态不影响主任务，也不负责测试或修复。

项目记忆互相隔离；只读取明确相关的共享偏好。当前摘要保留代码结构、UI 设计选择、文档组织和重要决定，不重复堆积任务记录。

## Skill

| Skill | 核心职责 |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | 受约束工作保留用户模型，独立工作自适应选模。 |
| [Workflow](workflow-skill/SKILL.md) | 明确目标、必要计划、安全并行。 |
| [Code](code-skill/SKILL.md) | 直接清晰的代码、明确职责、一致 UI。 |
| [Prompt](prompt-skill/SKILL.md) | 清晰的目标、限制、输入和输出。 |
| [Verify](verify-skill/SKILL.md) | 在完成前用最小相关证据验证。 |
| [Project Memory](project-memory-skill/SKILL.md) | 相关记忆读取与简洁持久摘要。 |
| [Optimization](optimization-skill/SKILL.md) | 按需简化，以实测支持结果。 |
| [Management](management-skill/SKILL.md) | 可恢复安装与授权发布。 |

## 安装或更新

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

Windows 使用 `py -3 -B`。安装以锁、备份和恢复机制替换八个托管 Skill，保留其他 Skill、用户 AGENTS 和私有路由历史。明确更新全局 AGENTS 时使用 `install-global-agents --source-dir .`，并生成可恢复备份。

源代码修改、本地安装和 GitHub 发布是不同结果。发布命令 `push` 在暂存或远端写入前运行当前发布检查。

## 代码规则归属

- `general` · general · `workflow-skill` · active · [rules](./task-analyze-skill/references/model-selection.md)
- `python` · code · `code-skill` · active · [rules](./code-skill/references/python-rules.md)
- `csharp` · code · `code-skill` · history-only · [rules](./code-skill/references/csharp-rules.md)
- `unity_csharp` · code · `code-skill` · active · [rules](./code-skill/references/unity-csharp-rules.md)
- `code_unspecified` · code · `code-skill` · history-only · [rules](./code-skill/references/legacy-code-unspecified.md)

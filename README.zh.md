# qin-codex-skills

精简的全局 Skill：代码结构、UI 偏好、任务协作与项目记忆。

用户选择的模型负责阅读相关 Skill 和项目记忆，理解任务并定义各子任务目标。受 Skill 约束的工作保留用户选择的**模型和推理强度**；独立且不受 Skill 约束的常规工作仍可自适应选模。纯工具调用无需额外模型。

## 工作流程

1. 读取相关 Skill 和当前项目记忆；记忆缺失直接跳过。
2. 展示任务评分、模型/推理强度和路由；子任务展示目标、评分、模型、依赖和结果。简单任务直接执行；需要时计划依赖，把独立目标交给写入范围清晰的子任务。
3. 在当前任务内验证重要改动，选择能证明行为的最小检查。简单数值修改默认跳过。只有用户要求相应范围时才启动或编译整个项目。
4. 完成后用用户选择的模型总结值得保留的信息。按用户授权的流程创建独立、可见、无项目绑定的 Ending 记忆任务，展示任务链接和记忆回读。Ending 只更新记忆，不验证、不修复、不跑基准。

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

## 实测与基准

八次真实 Astra/ultra 调用修复了隔离的示例界面和跨平台进程函数，并计算精确汇总。输出、实际模型、Skill 阅读和渲染检查均通过；其中一次阅读证据被检测器误判，已根据原始完整文件输出更正，原始失败仍保留。

| 对比 | 无 Skill：token / 秒 | 安装 Skill：token / 秒 | 结果 |
| --- | ---: | ---: | --- |
| 原版，三组配对 | 768,610 / 752.11 | 1,113,558 / 988.72 | token 多 44.88%，耗时多 31.46% |
| 精简重复验证后，一组配对 | 271,203 / 278.46 | 344,268 / 310.86 | token 多 26.94%，耗时多 11.63% |

**本次基准没有证明节省。** token 包含缓存输入。两组收到同一份完整明确的任务说明；样本、缓存和延迟限制结论，且本次单模型对比不衡量自适应选模或记忆生命周期的节省。独立真实工作流已验证：受规则约束的审查用 Astra/ultra，独立计算用 Luna/low，两者并行；汇总和可见的记忆 Ending 均用 Astra/ultra。Windows 原生预检 73 项通过，1 项按平台预期跳过。

八个入口文件由 24,126 词精简到 3,777 词，减少 84.34%；文本缩减不等于执行节省。[全部实测、模型分工、失败记录和统计边界](management-skill/assets/readme/current-workflow-benchmark.md)。

## 代码规则归属

- `general` · general · `workflow-skill` · active · [rules](./task-analyze-skill/references/model-selection.md)
- `python` · code · `code-skill` · active · [rules](./code-skill/references/python-rules.md)
- `csharp` · code · `code-skill` · history-only · [rules](./code-skill/references/csharp-rules.md)
- `unity_csharp` · code · `code-skill` · active · [rules](./code-skill/references/unity-csharp-rules.md)
- `code_unspecified` · code · `code-skill` · history-only · [rules](./code-skill/references/spark-small-code.md)
